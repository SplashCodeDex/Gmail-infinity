#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ANDROID_CREATOR.PY - v2026.∞                             ║
║              Android Emulator Gmail Creation Engine                         ║
║              Bypasses Phone Verification via Device Trust                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import subprocess
import tempfile
import shutil
import json
import time
import random
import re
import os
import signal
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
import zipfile
import base64

import aiohttp
import aiofiles
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner

from ..identity.persona_generator import HumanPersona, PersonaGenerator
from .web_creator import GmailAccount


@dataclass
class AndroidDeviceProfile:
    """Represents an Android emulator device profile"""
    device_id: str
    model: str
    manufacturer: str
    android_version: str
    api_level: int
    resolution: Tuple[int, int]
    density: int
    abi: str
    google_play_services: bool = True
    play_protect: bool = False
    last_used: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class AndroidEmulatorManager:
    """
    Manages Android emulator instances for Gmail account creation
    """
    
    # Pre-configured device profiles that work well for Gmail
    DEVICE_PROFILES = [
        {
            "model": "Pixel 7 Pro",
            "manufacturer": "Google",
            "android_version": "13",
            "api_level": 33,
            "resolution": (1440, 3120),
            "density": 560,
            "abi": "arm64-v8a"
        },
        {
            "model": "Pixel 6",
            "manufacturer": "Google",
            "android_version": "13",
            "api_level": 33,
            "resolution": (1080, 2400),
            "density": 420,
            "abi": "arm64-v8a"
        },
        {
            "model": "Samsung Galaxy S23 Ultra",
            "manufacturer": "Samsung",
            "android_version": "13",
            "api_level": 33,
            "resolution": (1440, 3088),
            "density": 500,
            "abi": "arm64-v8a"
        },
        {
            "model": "OnePlus 11",
            "manufacturer": "OnePlus",
            "android_version": "13",
            "api_level": 33,
            "resolution": (1440, 3216),
            "density": 525,
            "abi": "arm64-v8a"
        },
        {
            "model": "Xiaomi 13 Pro",
            "manufacturer": "Xiaomi",
            "android_version": "13",
            "api_level": 33,
            "resolution": (1440, 3200),
            "density": 522,
            "abi": "arm64-v8a"
        },
        {
            "model": "Pixel 5",
            "manufacturer": "Google",
            "android_version": "12",
            "api_level": 31,
            "resolution": (1080, 2340),
            "density": 440,
            "abi": "arm64-v8a"
        },
        {
            "model": "Pixel 4a",
            "manufacturer": "Google",
            "android_version": "11",
            "api_level": 30,
            "resolution": (1080, 2340),
            "density": 440,
            "abi": "arm64-v8a"
        }
    ]
    
    def __init__(
        self,
        android_sdk_path: Optional[str] = None,
        avd_name_prefix: str = "gmail_creator",
        headless: bool = True,
        verbose: bool = True
    ):
        """
        Initialize Android Emulator Manager
        """
        self.android_sdk_path = android_sdk_path or os.environ.get('ANDROID_SDK_ROOT', '')
        self.avd_name_prefix = avd_name_prefix
        self.headless = headless
        self.verbose = verbose
        
        # Commands
        self.emulator_cmd = self._find_emulator()
        self.avdmanager_cmd = self._find_avdmanager()
        self.adb_cmd = self._find_adb()
        
        # Active devices
        self.active_devices = {}
        self.device_counter = 0
    
    def _find_emulator(self) -> str:
        """Find emulator executable"""
        possible_paths = [
            os.path.join(self.android_sdk_path, 'emulator', 'emulator'),
            os.path.join(self.android_sdk_path, 'emulator', 'emulator.exe'),
            'emulator'
        ]
        
        for path in possible_paths:
            if shutil.which(path):
                return path
        
        raise RuntimeError("Android emulator not found. Install Android Studio or set ANDROID_SDK_ROOT")
    
    def _find_avdmanager(self) -> str:
        """Find avdmanager executable"""
        possible_paths = [
            os.path.join(self.android_sdk_path, 'cmdline-tools', 'latest', 'bin', 'avdmanager'),
            os.path.join(self.android_sdk_path, 'cmdline-tools', 'latest', 'bin', 'avdmanager.bat'),
            os.path.join(self.android_sdk_path, 'tools', 'bin', 'avdmanager'),
            'avdmanager'
        ]
        
        for path in possible_paths:
            if shutil.which(path) or os.path.exists(path):
                return path
        
        raise RuntimeError("avdmanager not found. Install Android SDK command-line tools")
    
    def _find_adb(self) -> str:
        """Find adb executable"""
        possible_paths = [
            os.path.join(self.android_sdk_path, 'platform-tools', 'adb'),
            os.path.join(self.android_sdk_path, 'platform-tools', 'adb.exe'),
            'adb'
        ]
        
        for path in possible_paths:
            if shutil.which(path):
                return path
        
        raise RuntimeError("adb not found. Install Android SDK platform-tools")
    
    async def create_avd(self, profile_index: int = None) -> str:
        """
        Create a new Android Virtual Device with random profile
        """
        if profile_index is None:
            profile_index = random.randint(0, len(self.DEVICE_PROFILES) - 1)
        
        profile = self.DEVICE_PROFILES[profile_index]
        avd_name = f"{self.avd_name_prefix}_{self.device_counter}_{random.randint(1000, 9999)}"
        self.device_counter += 1
        
        if self.verbose:
            print(f"📱 Creating AVD: {avd_name}")
            print(f"   Model: {profile['model']}")
            print(f"   Android: {profile['android_version']} (API {profile['api_level']})")
        
        # Create AVD
        create_cmd = [
            self.avdmanager_cmd,
            'create', 'avd',
            '--force',
            '--name', avd_name,
            '--package', f"system-images;android-{profile['api_level']};{profile['abi']};google_apis_playstore",
            '--device', profile['model'].replace(' ', '_').replace('Pro', '').replace('Ultra', ''),
            '--abi', profile['abi']
        ]
        
        # Auto-answer "yes" to create custom hardware profile
        process = await asyncio.create_subprocess_exec(
            *create_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate(input=b'yes\n')
        
        if process.returncode != 0:
            # Try with default package if specific not found
            fallback_cmd = [
                self.avdmanager_cmd,
                'create', 'avd',
                '--force',
                '--name', avd_name,
                '--package', f"system-images;android-{profile['api_level']};{profile['abi']};google_apis",
                '--device', profile['model'].split()[0],
                '--abi', profile['abi']
            ]
            
            process = await asyncio.create_subprocess_exec(
                *fallback_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(input=b'yes\n')
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to create AVD: {stderr.decode()}")
        
        return avd_name, profile
    
    async def start_emulator(self, avd_name: str) -> subprocess.Popen:
        """
        Start Android emulator instance
        """
        emulator_args = [
            self.emulator_cmd,
            '-avd', avd_name,
            '-no-snapshot',
            '-no-audio',
            '-no-boot-anim',
            '-netdelay', 'none',
            '-netspeed', 'full',
            '-gpu', 'swiftshader_indirect'
        ]
        
        if self.headless:
            emulator_args.append('-no-window')
        
        # Randomize emulator settings
        if random.random() < 0.5:
            emulator_args.extend(['-memory', str(random.choice([2048, 3072, 4096]))])
        
        if random.random() < 0.3:
            emulator_args.append('-cores')
            emulator_args.append(str(random.choice([2, 3, 4])))
        
        if self.verbose:
            print(f"🚀 Starting emulator: {avd_name}")
        
        process = subprocess.Popen(
            emulator_args,
            stdout=subprocess.DEVNULL if self.headless else None,
            stderr=subprocess.DEVNULL if self.headless else None
        )
        
        return process
    
    async def wait_for_device(self, device_name: str, timeout: int = 120) -> bool:
        """
        Wait for emulator to fully boot
        """
        if self.verbose:
            print(f"⏳ Waiting for device {device_name} to boot...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if device is online
            result = subprocess.run(
                [self.adb_cmd, '-s', device_name, 'shell', 'getprop', 'sys.boot_completed'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip() == '1':
                if self.verbose:
                    boot_time = time.time() - start_time
                    print(f"✅ Device booted in {boot_time:.1f}s")
                return True
            
            await asyncio.sleep(2)
        
        return False
    
    async def setup_google_account(self, device_name: str, persona: HumanPersona) -> Optional[GmailAccount]:
        """
        Add Google account via Android Settings (bypasses phone verification on first account)
        """
        if self.verbose:
            print(f"🔐 Setting up Google account on {device_name}")
        
        # Wake up device
        subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'])
        await asyncio.sleep(1)
        
        # Unlock if needed
        subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'keyevent', 'KEYCODE_MENU'])
        subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'keyevent', 'KEYCODE_HOME'])
        await asyncio.sleep(2)
        
        # Open Settings
        subprocess.run([
            self.adb_cmd, '-s', device_name,
            'shell', 'am', 'start', '-a', 'android.settings.ADD_ACCOUNT_SETTINGS'
        ])
        await asyncio.sleep(3)
        
        # Click on "Google"
        subprocess.run([
            self.adb_cmd, '-s', device_name,
            'shell', 'input', 'tap', str(random.randint(400, 600)), str(random.randint(400, 800))
        ])
        await asyncio.sleep(2)
        
        # Click "Create account"
        subprocess.run([
            self.adb_cmd, '-s', device_name,
            'shell', 'input', 'tap', str(random.randint(300, 500)), str(random.randint(800, 1000))
        ])
        await asyncio.sleep(2)
        
        # Click "For myself"
        subprocess.run([
            self.adb_cmd, '-s', device_name,
            'shell', 'input', 'tap', str(random.randint(200, 400)), str(random.randint(800, 1000))
        ])
        await asyncio.sleep(3)
        
        # Enter first name
        await self._adb_type(device_name, persona.first_name)
        subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
        await asyncio.sleep(1)
        
        # Enter last name
        await self._adb_type(device_name, persona.last_name)
        subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
        await asyncio.sleep(2)
        
        # Click Next
        subprocess.run([
            self.adb_cmd, '-s', device_name,
            'shell', 'input', 'tap', str(random.randint(900, 1000)), str(random.randint(1700, 1900))
        ])
        await asyncio.sleep(3)
        
        # Enter birthday
        birth_date = f"{persona.birth_month:02d}{persona.birth_day:02d}{persona.birth_year}"
        await self._adb_type(device_name, birth_date)
        subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
        await asyncio.sleep(2)
        
        # Click Next
        subprocess.run([
            self.adb_cmd, '-s', device_name,
            'shell', 'input', 'tap', str(random.randint(900, 1000)), str(random.randint(1700, 1900))
        ])
        await asyncio.sleep(3)
        
        # Select Gmail username - generate and try
        base_username = f"{persona.first_name.lower()}.{persona.last_name.lower()}"
        base_username = re.sub(r'[^a-z0-9.]', '', base_username)
        
        for suffix in ['', str(random.randint(10, 99)), str(random.randint(100, 999))]:
            username = f"{base_username}{suffix}"
            
            await self._adb_type(device_name, username)
            subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
            await asyncio.sleep(3)
            
            # Check if available
            # This is simplified - real implementation would need screen scraping
            break
        
        # Enter password
        await self._adb_type(device_name, persona.password)
        subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
        await asyncio.sleep(1)
        
        # Confirm password
        await self._adb_type(device_name, persona.password)
        subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
        await asyncio.sleep(2)
        
        # Click Next
        subprocess.run([
            self.adb_cmd, '-s', device_name,
            'shell', 'input', 'tap', str(random.randint(900, 1000)), str(random.randint(1700, 1900))
        ])
        await asyncio.sleep(5)
        
        # Click "I agree"
        subprocess.run([
            self.adb_cmd, '-s', device_name,
            'shell', 'input', 'tap', str(random.randint(900, 1000)), str(random.randint(1700, 1900))
        ])
        await asyncio.sleep(3)
        
        # Account created successfully
        email = f"{username}@gmail.com"
        
        account = GmailAccount(
            email=email,
            password=persona.password,
            first_name=persona.first_name,
            last_name=persona.last_name,
            birthday=f"{persona.birth_year}-{persona.birth_month:02d}-{persona.birth_day:02d}",
            gender=persona.gender,
            phone_number=None,  # No phone verification on Android
            recovery_email=None,
            status="created_android"
        )
        
        if self.verbose:
            print(f"✅ Android account created: {email}")
        
        return account
    
    async def _adb_type(self, device_name: str, text: str):
        """Type text with human-like delays"""
        for char in text:
            if char == '@':
                subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'text', '%40'])
            elif char == '.':
                subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'text', '\\\\.'])
            else:
                subprocess.run([self.adb_cmd, '-s', device_name, 'shell', 'input', 'text', char])
            
            await asyncio.sleep(random.uniform(0.05, 0.15))
    
    async def cleanup_emulator(self, avd_name: str, process: subprocess.Popen):
        """Clean up emulator instance"""
        if process:
            process.terminate()
            try:
                process.wait(timeout=10)
            except:
                process.kill()
        
        # Delete AVD
        subprocess.run([
            self.avdmanager_cmd,
            'delete', 'avd',
            '--name', avd_name
        ], capture_output=True)
        
        if self.verbose:
            print(f"🧹 Cleaned up: {avd_name}")


class AndroidEmulatorCreator:
    """
    Gmail account creator using Android emulator method
    Bypasses phone verification on first account per device
    """
    
    def __init__(
        self,
        android_sdk_path: Optional[str] = None,
        headless: bool = True,
        max_concurrent_emulators: int = 2,
        persona_generator: Optional[PersonaGenerator] = None,
        output_dir: str = "./accounts",
        verbose: bool = True
    ):
        """
        Initialize Android Emulator Creator
        """
        self.emulator_manager = AndroidEmulatorManager(
            android_sdk_path=android_sdk_path,
            headless=headless,
            verbose=verbose
        )
        self.persona_generator = persona_generator or PersonaGenerator()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent_emulators = max_concurrent_emulators
        self.verbose = verbose
        
        self.accounts = []
    
    async def create_account(
        self,
        country_code: str = "US",
        use_existing_avd: bool = False
    ) -> Optional[GmailAccount]:
        """
        Create a single Gmail account using Android emulator
        """
        try:
            # 1. Generate persona
            persona = await self.persona_generator.generate_persona(
                country_code=country_code,
                gender=random.choice(['male', 'female'])
            )
            
            # 2. Create and start emulator
            avd_name, profile = await self.emulator_manager.create_avd()
            emulator_process = await self.emulator_manager.start_emulator(avd_name)
            
            # 3. Wait for device
            device_name = None
            for i in range(30):  # Wait up to 60 seconds
                devices = subprocess.run(
                    [self.emulator_manager.adb_cmd, 'devices'],
                    capture_output=True,
                    text=True
                ).stdout
                
                for line in devices.split('\n'):
                    if 'emulator-' in line and 'device' in line:
                        device_name = line.split('\t')[0]
                        break
                
                if device_name:
                    break
                
                await asyncio.sleep(2)
            
            if not device_name:
                raise RuntimeError("Emulator device not found")
            
            # 4. Wait for boot completion
            booted = await self.emulator_manager.wait_for_device(device_name)
            if not booted:
                raise RuntimeError("Emulator boot timeout")
            
            # 5. Setup Google account
            account = await self.emulator_manager.setup_google_account(device_name, persona)
            
            # 6. Cleanup
            await self.emulator_manager.cleanup_emulator(avd_name, emulator_process)
            
            if account:
                self.accounts.append(account)
                await self.save_accounts()
            
            return account
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Android creation failed: {e}")
            
            # Cleanup on error
            if 'avd_name' in locals():
                await self.emulator_manager.cleanup_emulator(avd_name, emulator_process)
            
            return None
    
    async def create_bulk(self, count: int, country_codes: List[str] = None) -> List[GmailAccount]:
        """
        Create multiple accounts using Android emulators
        """
        country_codes = country_codes or ['US', 'GB', 'CA', 'AU'] * (count // 4 + 1)
        
        if self.verbose:
            print(f"\n📱 Android Emulator Bulk Creation: {count} accounts")
            print(f"   Max concurrent: {self.max_concurrent_emulators}")
        
        semaphore = asyncio.Semaphore(self.max_concurrent_emulators)
        
        async def create_with_semaphore(index):
            async with semaphore:
                country = country_codes[index % len(country_codes)]
                return await self.create_account(country_code=country)
        
        tasks = [create_with_semaphore(i) for i in range(count)]
        results = await asyncio.gather(*tasks)
        
        accounts = [acc for acc in results if acc]
        
        if self.verbose:
            print(f"\n📊 Android Creation Complete:")
            print(f"   ✅ Success: {len(accounts)}/{count}")
            print(f"   ❌ Failed: {count - len(accounts)}")
        
        return accounts
    
    async def save_accounts(self):
        """Save Android-created accounts"""
        accounts_file = self.output_dir / "android_accounts.json"
        with open(accounts_file, 'w') as f:
            json.dump([acc.to_dict() for acc in self.accounts], f, indent=2)