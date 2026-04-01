#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GMAIL-∞ CORE INITIALIZATION v2026.∞                       ║
║                  Quantum Email Factory - Core System Forge                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

__version__ = "2026.∞-quantum"
__author__ = "ARCHITECT-GMAIL"
__license__ = "Proprietary - Shadow Core Technology"

from .stealth_browser import (
    StealthBrowser,
    BrowserType,
    StealthConfig,
    FingerprintInjector,
    WebGLProtector,
    CanvasProtector,
    WebRTCBlocker,
    TimezoneSpoofer,
    GeolocationSpoofer,
    FontProtector,
    AudioProtector
)

from .behavior_engine import (
    BehaviorEngine,
    HumanBehaviorSimulator,
    TypingSimulator,
    MouseMovementSimulator,
    ScrollSimulator,
    ClickSimulator,
    FormFillingSimulator,
    ReadingTimeSimulator
)

from .proxy_manager import (
    ProxyManager,
    ProxyType,
    ProxyHealthChecker,
    ProxyRotator,
    ResidentialProxyFetcher,
    MobileProxyFetcher,
    IPv6Rotator,
    ProxyAnonymizer
)

from .fingerprint_generator import (
    QuantumFingerprintFactory,
    QuantumFingerprint,
    GPUProfileGenerator,
    CanvasFingerprintGenerator,
    SystemFontGenerator,
    BrowserProfileGenerator,
    HardwareProfileGenerator,
    TimezoneGenerator,
    LanguageGenerator,
    AudioFingerprintGenerator,
    PluginGenerator
)

from .detection_evasion import (
    DetectionEvasionEngine,
    GoogleBotDetector,
    MLAnomalyPreventer,
    WebDriverDetector,
    AutomationFlagRemover,
    PermissionSimulator,
    NavigatorManipulator,
    ChromeRuntimeInjector,
    MemoryTimingProtector
)

__all__ = [
    # Stealth Browser
    'StealthBrowser',
    'BrowserType',
    'StealthConfig',
    'FingerprintInjector',
    'WebGLProtector',
    'CanvasProtector',
    'WebRTCBlocker',
    'TimezoneSpoofer',
    'GeolocationSpoofer',
    'FontProtector',
    'AudioProtector',
    
    # Behavior Engine
    'BehaviorEngine',
    'HumanBehaviorSimulator',
    'TypingSimulator',
    'MouseMovementSimulator',
    'ScrollSimulator',
    'ClickSimulator',
    'FormFillingSimulator',
    'ReadingTimeSimulator',
    
    # Proxy Manager
    'ProxyManager',
    'ProxyType',
    'ProxyHealthChecker',
    'ProxyRotator',
    'ResidentialProxyFetcher',
    'MobileProxyFetcher',
    'IPv6Rotator',
    'ProxyAnonymizer',
    
    # Fingerprint Generator
    'QuantumFingerprintFactory',
    'QuantumFingerprint',
    'GPUProfileGenerator',
    'CanvasFingerprintGenerator',
    'SystemFontGenerator',
    'BrowserProfileGenerator',
    'HardwareProfileGenerator',
    'TimezoneGenerator',
    'LanguageGenerator',
    'AudioFingerprintGenerator',
    'PluginGenerator',
    
    # Detection Evasion
    'DetectionEvasionEngine',
    'GoogleBotDetector',
    'MLAnomalyPreventer',
    'WebDriverDetector',
    'AutomationFlagRemover',
    'PermissionSimulator',
    'NavigatorManipulator',
    'ChromeRuntimeInjector',
    'MemoryTimingProtector'
]