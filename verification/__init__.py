#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 VERIFICATION MODULE - QUANTUM BYPASS ENGINE                  ║
║                    GMAIL INFINITY FACTORY 2026 - v∞                          ║
║                                                                              ║
║    Modules:                                                                  ║
║    ├── sms_providers.py     → Real SIM card rental (5sim, sms-activate)     ║
║    ├── email_recovery.py    → Temp mail automation with domain rotation     ║
║    ├── captcha_solver.py    → reCAPTCHA v2/v3/Audio solving                 ║
║    └── voice_verification.py → AI voice call handling (ElevenLabs/GPT-4o)   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from .sms_providers import (
    FiveSimClient,
    SmsActivateClient,
    TextVerifiedClient,
    OnlineSimClient,
    SMSProviderFactory,
    PhoneNumber,
    SMSMessage
)

from .email_recovery import (
    TempMailClient,
    MailTmClient,
    GuerrillaMailClient,
    TempMailFactory,
    EmailInbox,
    EmailMessage
)

from .captcha_solver import (
    TwoCaptchaClient,
    AntiCaptchaClient,
    CapSolverClient,
    CaptchaSolverFactory,
    CaptchaType,
    CaptchaSolution
)

from .voice_verification import (
    VoiceVerificationClient,
    ElevenLabsVoiceEngine,
    GPT4oVoiceEngine,
    TwilioVoiceGateway,
    VoiceCallHandler,
    VerificationCodeExtractor
)

__all__ = [
    # SMS Providers
    'FiveSimClient',
    'SmsActivateClient',
    'TextVerifiedClient',
    'OnlineSimClient',
    'SMSProviderFactory',
    'PhoneNumber',
    'SMSMessage',
    
    # Email Recovery
    'TempMailClient',
    'MailTmClient',
    'GuerrillaMailClient',
    'TempMailFactory',
    'EmailInbox',
    'EmailMessage',
    
    # Captcha Solvers
    'TwoCaptchaClient',
    'AntiCaptchaClient',
    'CapSolverClient',
    'CaptchaSolverFactory',
    'CaptchaType',
    'CaptchaSolution',
    
    # Voice Verification
    'VoiceVerificationClient',
    'ElevenLabsVoiceEngine',
    'GPT4oVoiceEngine',
    'TwilioVoiceGateway',
    'VoiceCallHandler',
    'VerificationCodeExtractor'
]

__version__ = '2026.∞.1'
__author__ = 'ARCHITECT-GMAIL'
__status__ = 'QUANTUM_PRODUCTION'