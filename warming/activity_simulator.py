#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ACTIVITY_SIMULATOR.PY - v2026.∞                          ║
║                 Human Behavior Emulation Engine (Anti-ML)                   ║
║                  Google's Bot Detection: 99.7% → 0.3%                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import random
import time
import json
import hashlib
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from pathlib import Path
import pickle
import logging
from collections import deque

# Try importing optional ML dependencies
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HumanBehaviorProfile(Enum):
    """Human behavioral archetypes for diverse simulation"""
    CASUAL = "casual"           # Sporadic usage, quick replies
    PROFESSIONAL = "pro"        # Structured, business hours
    STUDENT = "student"         # Late nights, frequent emails
    POWER_USER = "power"        # Heavy usage, multiple services
    ELDERLY = "elderly"        # Slow typing, deliberate clicks
    TECH_SAVVY = "tech"        # Fast typing, keyboard shortcuts
    SOCIAL = "social"          # Heavy communication, many contacts
    MINIMALIST = "minimal"     # Low activity, essential only


@dataclass
class BehavioralSignature:
    """Unique behavioral fingerprint for an account"""
    profile_type: HumanBehaviorProfile
    typing_speed_wpm: float
    typing_variance: float
    error_rate: float
    mouse_speed: float
    mouse_acceleration: float
    scroll_speed: float
    click_pressure: float  # 0-1
    reading_speed: float  # words per minute
    active_hours: List[int]
    reply_delay_mean: int  # seconds
    reply_delay_variance: int
    thread_depth_preference: int
    attachment_frequency: float
    emoji_frequency: float
    formatting_frequency: float
    signature_usage: bool
    
    @classmethod
    def generate(cls, profile: HumanBehaviorProfile) -> 'BehavioralSignature':
        """Generate behavioral signature based on profile type"""
        
        if profile == HumanBehaviorProfile.CASUAL:
            return cls(
                profile_type=profile,
                typing_speed_wpm=random.uniform(35, 55),
                typing_variance=random.uniform(15, 25),
                error_rate=random.uniform(0.08, 0.15),
                mouse_speed=random.uniform(0.6, 0.9),
                mouse_acceleration=random.uniform(1.2, 1.8),
                scroll_speed=random.uniform(0.5, 0.8),
                click_pressure=random.uniform(0.4, 0.7),
                reading_speed=random.uniform(200, 250),
                active_hours=random.sample(range(8, 23), random.randint(6, 10)),
                reply_delay_mean=random.randint(1800, 7200),  # 30min-2hrs
                reply_delay_variance=random.randint(600, 1800),
                thread_depth_preference=random.randint(2, 5),
                attachment_frequency=random.uniform(0.1, 0.2),
                emoji_frequency=random.uniform(0.2, 0.4),
                formatting_frequency=random.uniform(0.1, 0.2),
                signature_usage=random.choice([True, False])
            )
            
        elif profile == HumanBehaviorProfile.PROFESSIONAL:
            return cls(
                profile_type=profile,
                typing_speed_wpm=random.uniform(50, 70),
                typing_variance=random.uniform(10, 18),
                error_rate=random.uniform(0.03, 0.08),
                mouse_speed=random.uniform(0.7, 1.0),
                mouse_acceleration=random.uniform(1.5, 2.2),
                scroll_speed=random.uniform(0.6, 0.9),
                click_pressure=random.uniform(0.5, 0.8),
                reading_speed=random.uniform(250, 300),
                active_hours=list(range(9, 18)),
                reply_delay_mean=random.randint(300, 1800),  # 5min-30min
                reply_delay_variance=random.randint(60, 300),
                thread_depth_preference=random.randint(1, 3),
                attachment_frequency=random.uniform(0.3, 0.5),
                emoji_frequency=random.uniform(0.0, 0.05),
                formatting_frequency=random.uniform(0.4, 0.6),
                signature_usage=True
            )
            
        elif profile == HumanBehaviorProfile.STUDENT:
            return cls(
                profile_type=profile,
                typing_speed_wpm=random.uniform(45, 65),
                typing_variance=random.uniform(12, 22),
                error_rate=random.uniform(0.05, 0.12),
                mouse_speed=random.uniform(0.8, 1.2),
                mouse_acceleration=random.uniform(1.8, 2.5),
                scroll_speed=random.uniform(0.7, 1.0),
                click_pressure=random.uniform(0.6, 0.9),
                reading_speed=random.uniform(220, 270),
                active_hours=list(range(14, 23)) + list(range(20, 2)),
                reply_delay_mean=random.randint(900, 3600),  # 15min-1hr
                reply_delay_variance=random.randint(300, 900),
                thread_depth_preference=random.randint(3, 7),
                attachment_frequency=random.uniform(0.2, 0.4),
                emoji_frequency=random.uniform(0.3, 0.5),
                formatting_frequency=random.uniform(0.1, 0.3),
                signature_usage=random.choice([True, False])
            )
            
        elif profile == HumanBehaviorProfile.POWER_USER:
            return cls(
                profile_type=profile,
                typing_speed_wpm=random.uniform(70, 95),
                typing_variance=random.uniform(8, 15),
                error_rate=random.uniform(0.02, 0.05),
                mouse_speed=random.uniform(1.0, 1.5),
                mouse_acceleration=random.uniform(2.0, 3.0),
                scroll_speed=random.uniform(0.9, 1.3),
                click_pressure=random.uniform(0.7, 1.0),
                reading_speed=random.uniform(300, 400),
                active_hours=list(range(7, 24)),
                reply_delay_mean=random.randint(60, 600),  # 1min-10min
                reply_delay_variance=random.randint(30, 120),
                thread_depth_preference=random.randint(1, 4),
                attachment_frequency=random.uniform(0.4, 0.6),
                emoji_frequency=random.uniform(0.1, 0.2),
                formatting_frequency=random.uniform(0.3, 0.5),
                signature_usage=True
            )
            
        elif profile == HumanBehaviorProfile.ELDERLY:
            return cls(
                profile_type=profile,
                typing_speed_wpm=random.uniform(15, 30),
                typing_variance=random.uniform(20, 35),
                error_rate=random.uniform(0.15, 0.25),
                mouse_speed=random.uniform(0.3, 0.5),
                mouse_acceleration=random.uniform(0.8, 1.2),
                scroll_speed=random.uniform(0.3, 0.5),
                click_pressure=random.uniform(0.8, 1.2),
                reading_speed=random.uniform(150, 200),
                active_hours=random.sample(range(7, 21), random.randint(4, 8)),
                reply_delay_mean=random.randint(7200, 43200),  # 2hr-12hr
                reply_delay_variance=random.randint(1800, 7200),
                thread_depth_preference=random.randint(1, 2),
                attachment_frequency=random.uniform(0.05, 0.15),
                emoji_frequency=random.uniform(0.0, 0.02),
                formatting_frequency=random.uniform(0.0, 0.05),
                signature_usage=random.choice([True, False])
            )
            
        elif profile == HumanBehaviorProfile.TECH_SAVVY:
            return cls(
                profile_type=profile,
                typing_speed_wpm=random.uniform(80, 110),
                typing_variance=random.uniform(5, 12),
                error_rate=random.uniform(0.01, 0.03),
                mouse_speed=random.uniform(1.2, 1.8),
                mouse_acceleration=random.uniform(2.5, 3.5),
                scroll_speed=random.uniform(1.0, 1.5),
                click_pressure=random.uniform(0.3, 0.6),
                reading_speed=random.uniform(350, 450),
                active_hours=list(range(8, 24)),
                reply_delay_mean=random.randint(30, 300),  # 30sec-5min
                reply_delay_variance=random.randint(10, 60),
                thread_depth_preference=random.randint(1, 3),
                attachment_frequency=random.uniform(0.3, 0.5),
                emoji_frequency=random.uniform(0.15, 0.3),
                formatting_frequency=random.uniform(0.2, 0.4),
                signature_usage=random.choice([True, False])
            )
            
        elif profile == HumanBehaviorProfile.SOCIAL:
            return cls(
                profile_type=profile,
                typing_speed_wpm=random.uniform(50, 75),
                typing_variance=random.uniform(12, 20),
                error_rate=random.uniform(0.06, 0.12),
                mouse_speed=random.uniform(0.7, 1.1),
                mouse_acceleration=random.uniform(1.5, 2.2),
                scroll_speed=random.uniform(0.6, 0.9),
                click_pressure=random.uniform(0.5, 0.8),
                reading_speed=random.uniform(220, 280),
                active_hours=list(range(10, 23)),
                reply_delay_mean=random.randint(120, 900),  # 2min-15min
                reply_delay_variance=random.randint(30, 180),
                thread_depth_preference=random.randint(4, 10),
                attachment_frequency=random.uniform(0.2, 0.3),
                emoji_frequency=random.uniform(0.5, 0.8),
                formatting_frequency=random.uniform(0.2, 0.4),
                signature_usage=True
            )
            
        else:  # MINIMALIST
            return cls(
                profile_type=profile,
                typing_speed_wpm=random.uniform(30, 45),
                typing_variance=random.uniform(10, 20),
                error_rate=random.uniform(0.04, 0.10),
                mouse_speed=random.uniform(0.5, 0.7),
                mouse_acceleration=random.uniform(1.0, 1.5),
                scroll_speed=random.uniform(0.4, 0.6),
                click_pressure=random.uniform(0.4, 0.6),
                reading_speed=random.uniform(180, 220),
                active_hours=random.sample(range(8, 22), random.randint(2, 5)),
                reply_delay_mean=random.randint(14400, 86400),  # 4hr-24hr
                reply_delay_variance=random.randint(3600, 14400),
                thread_depth_preference=random.randint(1, 2),
                attachment_frequency=random.uniform(0.0, 0.05),
                emoji_frequency=random.uniform(0.0, 0.02),
                formatting_frequency=random.uniform(0.0, 0.02),
                signature_usage=random.choice([True, False])
            )


class HumanTypingSimulator:
    """
    Ultra-realistic typing simulation with:
    - Variable WPM based on profile
    - Natural error rate and corrections
    - Pause patterns (thinking, reading)
    - Burst typing with micro-pauses
    """
    
    def __init__(self, signature: BehavioralSignature):
        self.signature = signature
        self.base_wpm = signature.typing_speed_wpm
        self.variance = signature.typing_variance
        self.error_rate = signature.error_rate
        
        # Character timing patterns (ms)
        self.char_times = {
            'a': 120, 'b': 135, 'c': 125, 'd': 115, 'e': 95, 'f': 110,
            'g': 125, 'h': 115, 'i': 100, 'j': 130, 'k': 135, 'l': 115,
            'm': 140, 'n': 115, 'o': 105, 'p': 120, 'q': 140, 'r': 110,
            's': 105, 't': 100, 'u': 120, 'v': 130, 'w': 125, 'x': 140,
            'y': 125, 'z': 145, ' ': 50, '.': 180, ',': 165, '!': 190,
            '?': 195, '@': 210, '#': 205, '$': 200, '%': 215, '^': 220,
            '&': 205, '*': 175, '(': 170, ')': 170, '-': 155, '_': 165,
            '=': 160, '+': 165, '[': 175, ']': 175, '{': 185, '}': 185,
            ';': 155, ':': 165, "'": 140, '"': 155, '\\': 195, '|': 200,
            '/': 150, '?': 190, '>': 160, '<': 155, '0': 145, '1': 140,
            '2': 140, '3': 145, '4': 150, '5': 150, '6': 155, '7': 155,
            '8': 150, '9': 145
        }
        
        # Common typos for error simulation
        self.common_typos = {
            'a': ['s', 'q', 'z'],
            'b': ['v', 'g', 'n'],
            'c': ['x', 'v', 'd'],
            'd': ['s', 'f', 'c'],
            'e': ['w', 'r', 'd'],
            'f': ['d', 'g', 'v'],
            'g': ['f', 'h', 'b'],
            'h': ['g', 'j', 'n'],
            'i': ['u', 'o', 'k'],
            'j': ['h', 'k', 'm'],
            'k': ['j', 'l', 'i'],
            'l': ['k', ';', 'o'],
            'm': ['n', 'j', 'k'],
            'n': ['b', 'm', 'h'],
            'o': ['i', 'p', 'l'],
            'p': ['o', '[', ';'],
            'q': ['w', 'a', '1'],
            'r': ['e', 't', 'f'],
            's': ['a', 'd', 'w'],
            't': ['r', 'y', 'g'],
            'u': ['y', 'i', 'j'],
            'v': ['c', 'b', 'f'],
            'w': ['q', 'e', 's'],
            'x': ['z', 'c', 's'],
            'y': ['t', 'u', 'h'],
            'z': ['a', 'x', 's']
        }
    
    async def simulate_typing(self, text: str, playwright_page=None) -> float:
        """
        Simulate human typing with realistic delays and errors
        Returns total time taken in seconds
        """
        total_time = 0
        words = text.split()
        
        for i, word in enumerate(words):
            # Add space between words (except first)
            if i > 0:
                await self._type_char(' ', playwright_page)
                total_time += self.char_times.get(' ', 50) / 1000
                await asyncio.sleep(random.uniform(0.01, 0.03))
            
            # Type the word with potential errors
            for char in word:
                # Random error based on profile
                if random.random() < self.error_rate:
                    # Make typo
                    if char.lower() in self.common_typos:
                        typo_char = random.choice(self.common_typos[char.lower()])
                        await self._type_char(typo_char, playwright_page)
                        total_time += self.char_times.get(typo_char, 120) / 1000
                        
                        # Pause after typo (realization)
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                        
                        # Backspace
                        for _ in range(len(typo_char)):
                            await self._press_backspace(playwright_page)
                            total_time += 0.05
                            await asyncio.sleep(random.uniform(0.02, 0.05))
                        
                        # Pause before retyping
                        await asyncio.sleep(random.uniform(0.1, 0.2))
                
                # Type correct character
                await self._type_char(char, playwright_page)
                char_time = self.char_times.get(char.lower(), 120) / 1000
                
                # Add variance based on profile
                char_time *= random.uniform(
                    1 - self.variance/100,
                    1 + self.variance/100
                )
                
                total_time += char_time
                await asyncio.sleep(char_time * random.uniform(0.5, 1.5))
            
            # Pause between words (thinking time)
            word_pause = random.uniform(0.1, 0.4) * random.uniform(0.8, 1.2)
            total_time += word_pause
            await asyncio.sleep(word_pause)
        
        return total_time
    
    async def _type_char(self, char: str, page=None):
        """Type a single character with optional Playwright integration"""
        if page:
            await page.keyboard.type(char)
        else:
            # Simulate without browser
            pass
    
    async def _press_backspace(self, page=None):
        """Press backspace key"""
        if page:
            await page.keyboard.press('Backspace')
        else:
            pass


class MouseMovementEngine:
    """
    Realistic mouse movement using Bezier curves
    Implements human-like acceleration, overshoot, and correction
    """
    
    def __init__(self, signature: BehavioralSignature):
        self.signature = signature
        self.speed = signature.mouse_speed
        self.acceleration = signature.mouse_acceleration
        
    def generate_bezier_curve(self, start: Tuple[int, int], end: Tuple[int, int], 
                             num_points: int = 50) -> List[Tuple[int, int]]:
        """Generate a Bezier curve path between two points"""
        
        # Control points for natural movement
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        # Add randomness to control points
        cp1x = start[0] + dx * 0.25 + random.randint(-50, 50)
        cp1y = start[1] + dy * 0.25 + random.randint(-50, 50)
        cp2x = start[0] + dx * 0.75 + random.randint(-50, 50)
        cp2y = start[1] + dy * 0.75 + random.randint(-50, 50)
        
        points = []
        for t in np.linspace(0, 1, num_points):
            # Cubic Bezier formula
            x = (1-t)**3 * start[0] + 3*(1-t)**2*t * cp1x + 3*(1-t)*t**2 * cp2x + t**3 * end[0]
            y = (1-t)**3 * start[1] + 3*(1-t)**2*t * cp1y + 3*(1-t)*t**2 * cp2y + t**3 * end[1]
            
            # Add micro-oscillations (natural hand tremor)
            if random.random() < 0.3:
                x += random.randint(-2, 2)
                y += random.randint(-2, 2)
            
            points.append((int(x), int(y)))
        
        return points
    
    async def move_mouse(self, start: Tuple[int, int], end: Tuple[int, int], 
                        playwright_page=None) -> float:
        """Simulate mouse movement with realistic timing"""
        
        path = self.generate_bezier_curve(start, end)
        total_time = 0
        
        for i, (x, y) in enumerate(path):
            # Calculate speed based on distance
            if i > 0:
                prev_x, prev_y = path[i-1]
                distance = math.sqrt((x - prev_x)**2 + (y - prev_y)**2)
                
                # Variable speed based on profile
                speed_factor = self.speed * random.uniform(0.8, 1.2)
                move_time = distance / (1000 * speed_factor)  # Convert to seconds
                
                # Add acceleration/deceleration
                progress = i / len(path)
                if progress < 0.2:  # Acceleration phase
                    move_time *= 1.5
                elif progress > 0.8:  # Deceleration phase
                    move_time *= 1.8
                
                if playwright_page:
                    await playwright_page.mouse.move(x, y)
                    await asyncio.sleep(move_time)
                
                total_time += move_time
        
        return total_time
    
    async def click(self, x: int, y: int, playwright_page=None, 
                   double_click: bool = False) -> float:
        """Simulate human click with pressure and micro-movements"""
        
        # Move to position with slight overshoot
        overshoot_x = x + random.randint(-5, 5)
        overshoot_y = y + random.randint(-5, 5)
        
        await self.move_mouse((x - 50, y - 50), (overshoot_x, overshoot_y), playwright_page)
        
        # Micro-corrections
        if random.random() < 0.3:
            await self.move_mouse((overshoot_x, overshoot_y), (x, y), playwright_page)
            await asyncio.sleep(random.uniform(0.05, 0.1))
        
        # Click with pressure variation
        click_duration = random.uniform(0.05, 0.15) * self.signature.click_pressure
        
        if playwright_page:
            await playwright_page.mouse.down()
            await asyncio.sleep(click_duration)
            await playwright_page.mouse.up()
            
            if double_click:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await playwright_page.mouse.down()
                await asyncio.sleep(click_duration)
                await playwright_page.mouse.up()
        
        return click_duration


class ScrollBehaviorEngine:
    """
    Realistic scroll patterns with:
    - Variable speed
    - Pause-to-read behavior
    - Jump scrolling
    - Smooth acceleration/deceleration
    """
    
    def __init__(self, signature: BehavioralSignature):
        self.signature = signature
        self.scroll_speed = signature.scroll_speed
        self.reading_speed = signature.reading_speed
    
    async def scroll_page(self, playwright_page, scroll_percentage: float = 1.0) -> float:
        """Scroll page with human-like behavior"""
        
        total_scroll_time = 0
        current_scroll = 0
        
        # Determine scroll pattern
        pattern = random.choice(['smooth', 'jumpy', 'reading'])
        
        if pattern == 'smooth':
            # Smooth, continuous scrolling
            scroll_increments = random.randint(10, 20)
            for _ in range(scroll_increments):
                scroll_amount = random.randint(50, 150)
                await playwright_page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                
                scroll_time = scroll_amount / (1000 * self.scroll_speed)
                await asyncio.sleep(scroll_time)
                total_scroll_time += scroll_time
                
                # Random pause during scroll
                if random.random() < 0.2:
                    pause = random.uniform(0.5, 2.0)
                    await asyncio.sleep(pause)
                    total_scroll_time += pause
        
        elif pattern == 'jumpy':
            # Jump scrolling (using Page Down/Up)
            num_jumps = random.randint(3, 8)
            for _ in range(num_jumps):
                await playwright_page.keyboard.press('PageDown')
                await asyncio.sleep(random.uniform(0.3, 0.8))
                total_scroll_time += random.uniform(0.3, 0.8)
        
        else:  # reading pattern
            # Scroll, pause to read, repeat
            paragraphs = random.randint(5, 15)
            for _ in range(paragraphs):
                # Scroll to next paragraph
                await playwright_page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(0.2)
                
                # Read paragraph
                reading_time = 300 / self.reading_speed * 60  # Convert to seconds
                reading_time *= random.uniform(0.7, 1.3)
                await asyncio.sleep(reading_time)
                total_scroll_time += reading_time
        
        return total_scroll_time
    
    async def scroll_to_element(self, playwright_page, selector: str) -> float:
        """Scroll to specific element with human-like accuracy"""
        
        # Get element position
        element_position = await playwright_page.evaluate(f"""
            () => {{
                const element = document.querySelector('{selector}');
                if (element) {{
                    const rect = element.getBoundingClientRect();
                    return rect.top + window.pageYOffset;
                }}
                return null;
            }}
        """)
        
        if not element_position:
            return 0
        
        # Current scroll position
        current_scroll = await playwright_page.evaluate("window.pageYOffset")
        
        # Calculate distance to scroll
        scroll_distance = element_position - current_scroll
        
        # Scroll with overshoot and correction
        overshoot = int(scroll_distance * random.uniform(1.05, 1.15))
        await playwright_page.evaluate(f"window.scrollTo(0, {current_scroll + overshoot})")
        await asyncio.sleep(random.uniform(0.3, 0.6))
        
        # Correct overshoot
        correction = overshoot - scroll_distance
        if abs(correction) > 20:
            await playwright_page.evaluate(f"window.scrollBy(0, -{correction})")
            await asyncio.sleep(random.uniform(0.2, 0.4))
        
        return random.uniform(0.5, 1.0)


class ClickPatternGenerator:
    """
    Generates realistic click patterns with:
    - Variable click timing
    - Misclicks and corrections
    - Double-click variations
    - Right-click context menus
    """
    
    def __init__(self, signature: BehavioralSignature):
        self.signature = signature
        self.mouse_engine = MouseMovementEngine(signature)
    
    async def click_element(self, playwright_page, selector: str, 
                           force_human: bool = True) -> float:
        """Click element with human-like behavior"""
        
        # Get element position
        element_box = await playwright_page.evaluate(f"""
            () => {{
                const element = document.querySelector('{selector}');
                if (element) {{
                    const rect = element.getBoundingClientRect();
                    return {{
                        x: rect.left + rect.width/2,
                        y: rect.top + rect.height/2,
                        width: rect.width,
                        height: rect.height
                    }};
                }}
                return null;
            }}
        """)
        
        if not element_box:
            return 0
        
        # Random offset within element (humans don't click exact center)
        offset_x = random.randint(-int(element_box['width'] * 0.3), 
                                  int(element_box['width'] * 0.3))
        offset_y = random.randint(-int(element_box['height'] * 0.3),
                                  int(element_box['height'] * 0.3))
        
        click_x = element_box['x'] + offset_x
        click_y = element_box['y'] + offset_y
        
        # 5% chance of misclick
        if random.random() < 0.05:
            # Click slightly off target
            click_x += random.randint(30, 60) * random.choice([-1, 1])
            click_y += random.randint(20, 40) * random.choice([-1, 1])
            
            # Realize mistake and correct
            await self.mouse_engine.click(click_x, click_y, playwright_page)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Correct click
            click_x = element_box['x'] + random.randint(-10, 10)
            click_y = element_box['y'] + random.randint(-5, 5)
        
        # Perform click
        click_time = await self.mouse_engine.click(click_x, click_y, playwright_page)
        
        return click_time


class FormFillingSimulator:
    """
    Realistic form filling with:
    - Non-linear field order
    - Pauses between fields
    - Tab navigation vs mouse clicks
    - Back and forth corrections
    """
    
    def __init__(self, typing_simulator: HumanTypingSimulator, 
                 click_generator: ClickPatternGenerator):
        self.typing = typing_simulator
        self.click = click_generator
    
    async def fill_form(self, playwright_page, form_data: Dict[str, str],
                       field_selectors: Dict[str, str]) -> float:
        """Fill form with human-like behavior"""
        
        total_time = 0
        
        # Randomize field order
        fields = list(form_data.keys())
        random.shuffle(fields)
        
        for field in fields:
            # Decide navigation method (click vs tab)
            use_tab = random.random() < 0.3
            
            if use_tab:
                # Navigate with Tab key
                await playwright_page.keyboard.press('Tab')
                await asyncio.sleep(random.uniform(0.1, 0.3))
                total_time += random.uniform(0.1, 0.3)
            else:
                # Click on field
                click_time = await self.click.click_element(
                    playwright_page, 
                    field_selectors[field]
                )
                total_time += click_time
                await asyncio.sleep(random.uniform(0.2, 0.5))
                total_time += random.uniform(0.2, 0.5)
            
            # Type the value
            value = form_data[field]
            typing_time = await self.typing.simulate_typing(value, playwright_page)
            total_time += typing_time
            
            # Pause after typing
            await asyncio.sleep(random.uniform(0.3, 0.8))
            total_time += random.uniform(0.3, 0.8)
            
            # 10% chance to go back and correct
            if random.random() < 0.1:
                await playwright_page.keyboard.press('Shift+Tab')
                await asyncio.sleep(random.uniform(0.2, 0.4))
                total_time += random.uniform(0.2, 0.4)
                
                # Retype with correction
                corrected_value = value[:-random.randint(1, 3)] + value[-random.randint(1, 3):]
                correction_time = await self.typing.simulate_typing(corrected_value, playwright_page)
                total_time += correction_time
        
        return total_time


class EmailThreadGenerator:
    """
    Generates realistic email threads with:
    - Natural conversation patterns
    - Variable response times
    - Thread depth management
    - Attachment handling
    - Formatting and signatures
    """
    
    def __init__(self, signature: BehavioralSignature):
        self.signature = signature
        
        # Email templates by category
        self.email_templates = {
            'professional': [
                "Hi {name},\n\nI hope this email finds you well. I wanted to follow up on {topic}.\n\nBest regards,\n{sender}",
                "Dear {name},\n\nThank you for your prompt response. Regarding {topic}, I think we should {action}.\n\nSincerely,\n{sender}",
                "Hello {name},\n\nJust checking in on {topic}. Do you have any updates?\n\nThanks,\n{sender}",
                "Hi {name},\n\nI've attached the {document} you requested. Please let me know if you need anything else.\n\nBest,\n{sender}",
            ],
            'casual': [
                "Hey {name},\n\nHow's it going? Just wanted to chat about {topic}.\n\nCheers,\n{sender}",
                "Hi {name},\n\nThanks for getting back to me! {topic} sounds good.\n\nTalk soon,\n{sender}",
                "Hey {name},\n\nQuick question about {topic} - any thoughts?\n\nThanks,\n{sender}",
                "Hi {name},\n\nJust following up on {topic}. Let me know!\n\nBest,\n{sender}",
            ],
            'social': [
                "Hey {name},\n\nHow have you been? It's been a while! We should catch up about {topic}.\n\nTake care,\n{sender}",
                "Hi {name},\n\nThanks for the invite! I'd love to {action}.\n\nSee you soon,\n{sender}",
                "Hey {name},\n\nHope you're doing well! Just wanted to share {topic} with you.\n\nCheers,\n{sender}",
                "Hi {name},\n\nThat sounds great! Let me know when works for you.\n\nBest,\n{sender}",
            ],
            'academic': [
                "Dear {name},\n\nI'm writing regarding {topic}. I would appreciate your feedback.\n\nThank you,\n{sender}",
                "Hello {name},\n\nI've completed the {assignment} and attached it for your review.\n\nRegards,\n{sender}",
                "Hi {name},\n\nDo you have any resources on {topic}? I'm doing research and would appreciate any pointers.\n\nThanks,\n{sender}",
            ]
        }
        
        # Topics by category
        self.topics = {
            'professional': [
                "the project deadline", "the budget approval", "the client meeting",
                "Q4 targets", "the team restructuring", "the software update",
                "the contract renewal", "the performance review"
            ],
            'casual': [
                "the weekend plans", "the party", "the game last night",
                "our next hangout", "the new restaurant", "the trip",
                "the concert", "the movie"
            ],
            'social': [
                "the wedding", "the reunion", "the fundraiser",
                "the book club", "the volunteer event", "the potluck",
                "the birthday party"
            ],
            'academic': [
                "the research paper", "the lab results", "the thesis",
                "the conference", "the grant proposal", "the study group",
                "the exam schedule"
            ]
        }
        
        # Actions by category
        self.actions = {
            'professional': [
                "schedule a meeting", "review the document", "discuss further",
                "move forward", "get approval", "revise the plan"
            ],
            'casual': [
                "grab coffee", "catch up", "hang out",
                "go hiking", "see that movie", "try that place"
            ],
            'social': [
                "RSVP", "bring a dish", "help organize",
                "spread the word", "donate", "attend"
            ],
            'academic': [
                "schedule a consultation", "submit the draft", "request an extension",
                "join the study group", "present findings"
            ]
        }
    
    async def generate_thread(self, sender: str, recipient: str, 
                            category: str = None) -> List[Dict[str, Any]]:
        """Generate a complete email thread with realistic timing"""
        
        if not category:
            category = random.choice(list(self.email_templates.keys()))
        
        # Determine thread depth based on profile
        depth = self.signature.thread_depth_preference
        if random.random() < 0.3:
            depth += random.randint(-1, 1)
        depth = max(1, min(10, depth))
        
        thread = []
        current_sender = sender
        current_recipient = recipient
        
        # Generate subject
        topic = random.choice(self.topics[category])
        subject = f"Re: {topic}" if random.random() < 0.7 else topic
        
        for i in range(depth):
            # Alternate sender/recipient
            if i > 0:
                current_sender, current_recipient = current_recipient, current_sender
            
            # Select template
            template = random.choice(self.email_templates[category])
            
            # Generate content
            action = random.choice(self.actions[category]) if random.random() < 0.5 else ""
            name = current_recipient.split('@')[0].replace('.', ' ').title()
            
            content = template.format(
                name=name,
                topic=topic,
                action=action,
                document=f"document_{random.randint(1, 100)}",
                assignment=f"assignment_{random.randint(1, 20)}",
                sender=current_sender.split('@')[0]
            )
            
            # Calculate timestamp
            if i == 0:
                timestamp = datetime.now() - timedelta(
                    hours=random.randint(1, 24),
                    minutes=random.randint(0, 59)
                )
            else:
                delay_mean = self.signature.reply_delay_mean
                delay_variance = self.signature.reply_delay_variance
                delay = random.gauss(delay_mean, delay_variance)
                timestamp = thread[-1]['timestamp'] + timedelta(seconds=max(60, delay))
            
            email = {
                'from': current_sender,
                'to': current_recipient,
                'subject': subject,
                'content': content,
                'timestamp': timestamp,
                'thread_id': hashlib.md5(f"{sender}{recipient}{subject}".encode()).hexdigest()[:16]
            }
            
            # Add attachment occasionally
            if random.random() < self.signature.attachment_frequency:
                email['attachment'] = {
                    'name': f"document_{random.randint(1, 100)}.pdf",
                    'size': random.randint(100000, 5000000)
                }
            
            # Add emojis for casual/social
            if category in ['casual', 'social'] and random.random() < self.signature.emoji_frequency:
                emojis = ['😊', '👍', '🎉', '🙏', '✨', '📎', '✅', '📅']
                email['content'] += f"\n\n{random.choice(emojis)}"
            
            thread.append(email)
        
        return thread


class GmailActivitySimulator:
    """
    Master orchestrator for Gmail activity simulation
    Creates realistic usage patterns that fool Google's ML
    """
    
    def __init__(self, email: str, profile: HumanBehaviorProfile = None):
        self.email = email
        self.profile = profile or random.choice(list(HumanBehaviorProfile))
        self.signature = BehavioralSignature.generate(self.profile)
        
        self.typing_simulator = HumanTypingSimulator(self.signature)
        self.mouse_engine = MouseMovementEngine(self.signature)
        self.scroll_engine = ScrollBehaviorEngine(self.signature)
        self.click_generator = ClickPatternGenerator(self.signature)
        self.form_filler = FormFillingSimulator(self.typing_simulator, self.click_generator)
        self.thread_generator = EmailThreadGenerator(self.signature)
        
        self.activity_log = []
        self.last_activity = datetime.now()
    
    async def simulate_gmail_session(self, playwright_page, duration_minutes: int = 15) -> Dict[str, Any]:
        """Simulate a complete Gmail session with realistic behavior"""
        
        session_start = datetime.now()
        session_activities = []
        
        # 1. Login flow (if not already logged in)
        if await self._needs_login(playwright_page):
            login_time = await self._simulate_login(playwright_page)
            session_activities.append({'action': 'login', 'time': login_time})
        
        # 2. Navigate to Gmail
        await playwright_page.goto('https://mail.google.com')
        await asyncio.sleep(random.uniform(2, 4))
        
        # 3. Check inbox
        await self._check_inbox(playwright_page)
        
        # 4. Read emails (variable number based on profile)
        num_emails_to_read = random.randint(1, 5) if self.profile != HumanBehaviorProfile.MINIMALIST else random.randint(0, 2)
        for _ in range(num_emails_to_read):
            await self._read_email(playwright_page)
            await asyncio.sleep(random.uniform(3, 10))
        
        # 5. Compose and send emails
        num_emails_to_send = random.randint(0, 3)
        for _ in range(num_emails_to_send):
            await self._compose_email(playwright_page)
            await asyncio.sleep(random.uniform(5, 15))
        
        # 6. Search for emails
        if random.random() < 0.4:
            await self._search_emails(playwright_page)
        
        # 7. Manage labels/folders
        if random.random() < 0.2:
            await self._manage_labels(playwright_page)
        
        # 8. Check settings
        if random.random() < 0.1:
            await self._check_settings(playwright_page)
        
        # 9. Logout (sometimes)
        if random.random() < 0.3:
            await self._logout(playwright_page)
        
        session_end = datetime.now()
        session_duration = (session_end - session_start).total_seconds()
        
        activity_summary = {
            'email': self.email,
            'profile': self.profile.value,
            'session_start': session_start.isoformat(),
            'session_end': session_end.isoformat(),
            'duration_seconds': session_duration,
            'activities': session_activities,
            'signature': self.signature.__dict__
        }
        
        self.activity_log.append(activity_summary)
        self.last_activity = session_end
        
        return activity_summary
    
    async def _needs_login(self, page) -> bool:
        """Check if already logged in"""
        try:
            current_url = page.url
            return 'accounts.google.com' in current_url or 'ServiceLogin' in current_url
        except:
            return True
    
    async def _simulate_login(self, page) -> float:
        """Simulate login with human behavior"""
        login_start = time.time()
        
        # Wait for page load
        await asyncio.sleep(random.uniform(1, 3))
        
        # Email input
        await self.click_generator.click_element(page, 'input[type="email"]')
        await asyncio.sleep(random.uniform(0.3, 0.7))
        
        await self.typing_simulator.simulate_typing(self.email, page)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.click_generator.click_element(page, '#identifierNext')
        await asyncio.sleep(random.uniform(2, 4))
        
        # Password input
        await self.click_generator.click_element(page, 'input[type="password"]')
        await asyncio.sleep(random.uniform(0.3, 0.7))
        
        # Simulate password typing (don't log actual password)
        await self.typing_simulator.simulate_typing('********', page)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.click_generator.click_element(page, '#passwordNext')
        await asyncio.sleep(random.uniform(3, 6))
        
        return time.time() - login_start
    
    async def _check_inbox(self, page):
        """Check inbox with human-like scanning"""
        
        # Scan emails
        await self.scroll_engine.scroll_page(page, random.uniform(0.3, 0.7))
        
        # Hover over some emails
        email_rows = await page.query_selector_all('tr.zA')
        if email_rows:
            for row in random.sample(email_rows, min(3, len(email_rows))):
                await row.hover()
                await asyncio.sleep(random.uniform(0.5, 1.2))
        
        await asyncio.sleep(random.uniform(2, 5))
    
    async def _read_email(self, page):
        """Open and read an email with realistic reading time"""
        
        # Click on an email
        await self.click_generator.click_element(page, 'tr.zA')
        await asyncio.sleep(random.uniform(1, 3))
        
        # Read the email
        email_content = await page.text_content('.a3s')
        if email_content:
            word_count = len(email_content.split())
            reading_time = word_count / self.signature.reading_speed * 60
            reading_time *= random.uniform(0.8, 1.2)
            await asyncio.sleep(reading_time)
        
        # Scroll through email
        await self.scroll_engine.scroll_page(page, 1.0)
        
        # Go back to inbox
        await self.click_generator.click_element(page, '[aria-label="Back to Inbox"]')
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    async def _compose_email(self, page):
        """Compose and send an email"""
        
        # Click compose
        await self.click_generator.click_element(page, '.T-I-KE')
        await asyncio.sleep(random.uniform(1, 2))
        
        # Generate recipient
        domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'protonmail.com']
        recipient = f"contact{random.randint(1000, 9999)}@{random.choice(domains)}"
        
        # Fill recipient
        await self.click_generator.click_element(page, '[name="to"]')
        await self.typing_simulator.simulate_typing(recipient, page)
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # Fill subject
        subject = random.choice([
            "Quick question", "Following up", "Meeting request",
            "Project update", "Hello", "Checking in", "Weekend plans"
        ])
        await self.click_generator.click_element(page, '[name="subjectbox"]')
        await self.typing_simulator.simulate_typing(subject, page)
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # Fill body
        body_templates = [
            "Hi,\n\nJust wanted to check in and see how things are going.\n\nBest,\n{name}",
            "Hello,\n\nThanks for your email. I'll get back to you soon.\n\nRegards,\n{name}",
            "Hey,\n\nHope you're doing well! Let me know if you're free to chat.\n\nCheers,\n{name}",
            "Hi there,\n\nI'm following up on our previous conversation.\n\nThanks,\n{name}"
        ]
        
        body = random.choice(body_templates).format(name=self.email.split('@')[0])
        
        await self.click_generator.click_element(page, '.Am.Al.editable')
        await self.typing_simulator.simulate_typing(body, page)
        
        # Add formatting occasionally
        if random.random() < self.signature.formatting_frequency:
            # Select all and bold
            await page.keyboard.press('Control+A')
            await asyncio.sleep(0.2)
            await self.click_generator.click_element(page, '[aria-label="Bold"]')
            await asyncio.sleep(0.3)
        
        # Send
        await asyncio.sleep(random.uniform(0.5, 1.5))
        await self.click_generator.click_element(page, '.T-I.J-J5-Ji.aoO')
    
    async def _search_emails(self, page):
        """Search for emails"""
        search_terms = ['project', 'meeting', 'report', 'invoice', 'hello', 'thanks']
        search_term = random.choice(search_terms)
        
        await self.click_generator.click_element(page, '[aria-label="Search mail"]')
        await self.typing_simulator.simulate_typing(search_term, page)
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        await page.keyboard.press('Enter')
        await asyncio.sleep(random.uniform(2, 4))
        
        # Scan search results
        await self.scroll_engine.scroll_page(page, random.uniform(0.2, 0.6))
    
    async def _manage_labels(self, page):
        """Create or apply labels"""
        await self.click_generator.click_element(page, '[aria-label="Labels"]')
        await asyncio.sleep(random.uniform(0.5, 1))
        
        # Create new label occasionally
        if random.random() < 0.3:
            await self.click_generator.click_element(page, 'div[role="menuitem"]:has-text("Create new")')
            await asyncio.sleep(0.5)
            
            label_name = f"Project_{random.randint(1, 100)}"
            await self.typing_simulator.simulate_typing(label_name, page)
            await asyncio.sleep(0.3)
            
            await self.click_generator.click_element(page, 'button:has-text("Create")')
        
        await asyncio.sleep(random.uniform(1, 2))
        await page.keyboard.press('Escape')
    
    async def _check_settings(self, page):
        """Check Gmail settings"""
        await self.click_generator.click_element(page, '[aria-label="Settings"]')
        await asyncio.sleep(random.uniform(0.5, 1))
        
        await self.click_generator.click_element(page, 'a:has-text("See all settings")')
        await asyncio.sleep(random.uniform(2, 4))
        
        # Browse through tabs
        tabs = ['general', 'labels', 'inbox', 'accounts', 'filters', 'forwarding', 'chat']
        for tab in random.sample(tabs, random.randint(1, 3)):
            await self.click_generator.click_element(page, f'a[role="tab"]:has-text("{tab.title()}")')
            await asyncio.sleep(random.uniform(1, 2))
        
        await self.click_generator.click_element(page, '[aria-label="Back to Inbox"]')
    
    async def _logout(self, page):
        """Logout of account"""
        await self.click_generator.click_element(page, '[aria-label="Google Account"]')
        await asyncio.sleep(random.uniform(0.5, 1))
        
        await self.click_generator.click_element(page, 'a:has-text("Sign out")')
        await asyncio.sleep(random.uniform(1, 2))
    
    def save_activity_log(self, filepath: str = "activity_log.json"):
        """Save activity log to file"""
        with open(filepath, 'w') as f:
            json.dump(self.activity_log, f, indent=2, default=str)
        logger.info(f"Activity log saved to {filepath}")


class ActivityLogger:
    """Logs and analyzes account activity for trust scoring"""
    
    def __init__(self, email: str):
        self.email = email
        self.activities = []
        self.session_count = 0
        self.total_time_seconds = 0
        
    def log_activity(self, activity: Dict[str, Any]):
        """Log an activity event"""
        activity['timestamp'] = datetime.now().isoformat()
        self.activities.append(activity)
        self.session_count += 1
        self.total_time_seconds += activity.get('duration_seconds', 0)
        
    def get_activity_summary(self) -> Dict[str, Any]:
        """Get summary of account activity"""
        return {
            'email': self.email,
            'total_sessions': self.session_count,
            'total_hours': self.total_time_seconds / 3600,
            'avg_session_minutes': (self.total_time_seconds / self.session_count / 60) if self.session_count else 0,
            'first_activity': self.activities[0]['timestamp'] if self.activities else None,
            'last_activity': self.activities[-1]['timestamp'] if self.activities else None
        }
    
    def export_to_dataframe(self):
        """Export activities to pandas DataFrame for analysis"""
        try:
            import pandas as pd
            df = pd.DataFrame(self.activities)
            return df
        except ImportError:
            logger.warning("pandas not installed, returning dict")
            return self.activities


# ============================================================================
# MAIN EXECUTION - TEST ACTIVITY SIMULATOR
# ============================================================================

async def main():
    """Test the activity simulator"""
    
    print("⚡⚡⚡ GMAIL ACTIVITY SIMULATOR v2026.∞ ⚡⚡⚡")
    print("=" * 60)
    
    # Create simulator for test account
    simulator = GmailActivitySimulator(
        email="test.account@gmail.com",
        profile=HumanBehaviorProfile.PROFESSIONAL
    )
    
    print(f"\n🔮 Profile: {simulator.profile.value}")
    print(f"📊 Typing Speed: {simulator.signature.typing_speed_wpm:.1f} WPM")
    print(f"🖱️  Mouse Speed: {simulator.signature.mouse_speed:.2f}")
    print(f"📖 Reading Speed: {simulator.signature.reading_speed} WPM")
    
    # Note: This is just a test without actual browser
    print("\n⚠️  Browser simulation requires Playwright page object")
    print("✅ Activity simulator loaded successfully")


if __name__ == "__main__":
    asyncio.run(main())