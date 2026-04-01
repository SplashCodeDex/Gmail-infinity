#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    BEHAVIOR_ENGINE.PY - v2026.∞                             ║
║              Human Simulation AI - Google's Worst Nightmare                 ║
║                                                                             ║
║  "The difference between a bot and a human is not intelligence,            ║
║   it's imperfection." - ARCHITECT-GMAIL 2026                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import random
import math
import time
import json
from typing import Tuple, List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import savgol_filter
from collections import deque
import hashlib


class HumanEmotion(Enum):
    """Human emotional states that affect behavior patterns"""
    NEUTRAL = "neutral"
    IMPATIENT = "impatient"
    CAREFUL = "careful"
    DISTRACTED = "distracted"
    CONFUSED = "confused"
    CONFIDENT = "confident"
    TIRED = "tired"
    FOCUSED = "focused"


class TypingStyle(Enum):
    """Different human typing patterns"""
    TOUCH_TYPER = "touch_typer"  # Fast, consistent
    HUNT_AND_PECK = "hunt_peck"  # Slow, irregular
    HYBRID = "hybrid"  # Mixed style
    THUMB_TYPER = "thumb_typer"  # Mobile-style typing


@dataclass
class MouseMovement:
    """Represents a single mouse movement with timing"""
    x: int
    y: int
    timestamp: float
    velocity: float
    acceleration: float
    jerk: float  # Rate of change of acceleration


@dataclass
class TypingEvent:
    """Represents a single keystroke with timing"""
    key: str
    timestamp: float
    dwell_time: float  # How long key was pressed
    flight_time: float  # Time between key presses
    error: bool  # Was this a typo that needed correction?


@dataclass
class ScrollEvent:
    """Represents a scroll action"""
    delta_y: int
    timestamp: float
    speed: float
    acceleration: float
    direction: str  # 'up' or 'down'


@dataclass
class ClickEvent:
    """Represents a mouse click"""
    x: int
    y: int
    timestamp: float
    button: str  # 'left', 'right', 'middle'
    pressure: float  # Simulated click pressure (0.3-1.0)
    misclick: bool  # Was this a misclick?


@dataclass
class GazePoint:
    """Simulated eye-tracking / attention focus"""
    x: int
    y: int
    timestamp: float
    duration: float  # How long gaze stayed here


class BezierCurveGenerator:
    """
    Generate human-like mouse movements using cubic Bezier curves
    Humans don't move in straight lines - they follow curved paths
    """
    
    @staticmethod
    def generate_bezier_path(
        start_x: int, start_y: int,
        end_x: int, end_y: int,
        num_points: int = 50
    ) -> List[Tuple[int, int, float]]:
        """
        Generate a natural curved path between two points
        Uses random control points to simulate human hand movement
        """
        # Generate random control points with natural bias
        control_1_x = start_x + (end_x - start_x) * random.uniform(0.2, 0.4)
        control_1_y = start_y + (end_y - start_y) * random.uniform(0.1, 0.3)
        control_2_x = start_x + (end_x - start_x) * random.uniform(0.6, 0.8)
        control_2_y = start_y + (end_y - start_y) * random.uniform(0.7, 0.9)
        
        # Add perpendicular offset for curved movement
        perp_offset = random.uniform(-50, 50)
        if random.choice([True, False]):
            control_1_y += perp_offset
            control_2_y -= perp_offset
        else:
            control_1_x += perp_offset
            control_2_x -= perp_offset
        
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            
            # Cubic Bezier formula
            x = (1 - t) ** 3 * start_x + \
                3 * (1 - t) ** 2 * t * control_1_x + \
                3 * (1 - t) * t ** 2 * control_2_x + \
                t ** 3 * end_x
                
            y = (1 - t) ** 3 * start_y + \
                3 * (1 - t) ** 2 * t * control_1_y + \
                3 * (1 - t) * t ** 2 * control_2_y + \
                t ** 3 * end_y
            
            # Add micro-jitter (hand tremor)
            x += random.gauss(0, 0.5)
            y += random.gauss(0, 0.5)
            
            # Calculate time with velocity profile
            # Humans accelerate then decelerate
            velocity_profile = 1 - abs(2 * t - 1) ** 1.5
            time_delta = velocity_profile * random.uniform(0.01, 0.03)
            
            points.append((int(x), int(y), time_delta))
        
        return points
    
    @staticmethod
    def smooth_path(points: List[Tuple[int, int, float]], window_size: int = 5) -> List[Tuple[int, int, float]]:
        """Apply Savitzky-Golay filter to smooth mouse path"""
        if len(points) < window_size:
            return points
        
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        times = [p[2] for p in points]
        
        # Smooth coordinates
        xs_smooth = savgol_filter(xs, window_size, 3)
        ys_smooth = savgol_filter(ys, window_size, 3)
        
        return [(int(xs_smooth[i]), int(ys_smooth[i]), times[i]) for i in range(len(points))]


class TypingBehaviorEngine:
    """
    Simulate human typing patterns with realistic:
    - Variable typing speed (80-120 WPM with natural variance)
    - Typo rate (5-15% depending on emotional state)
    - Correction patterns (backspace usage)
    - Dwell time (how long keys are held)
    - Flight time (time between keystrokes)
    """
    
    # Typing speed by style (words per minute)
    TYPING_SPEEDS = {
        TypingStyle.TOUCH_TYPER: {
            'mean': 105,
            'std': 15,
            'min': 80,
            'max': 130
        },
        TypingStyle.HYBRID: {
            'mean': 75,
            'std': 12,
            'min': 60,
            'max': 95
        },
        TypingStyle.HUNT_AND_PECK: {
            'mean': 45,
            'std': 10,
            'min': 30,
            'max': 65
        },
        TypingStyle.THUMB_TYPER: {
            'mean': 55,
            'std': 12,
            'min': 40,
            'max': 75
        }
    }
    
    # Dwell time by key type (milliseconds)
    DWELL_TIMES = {
        'letter': (80, 120),  # Normal letters
        'space': (60, 100),    # Space bar
        'enter': (120, 200),   # Enter key
        'backspace': (90, 150), # Backspace
        'shift': (150, 250),   # Shift key
        'caps': (130, 180),    # Caps lock
        'number': (85, 130),   # Numbers
        'symbol': (95, 145),   # Symbols
        'function': (110, 170) # Function keys
    }
    
    # Typo patterns by keyboard region
    TYPO_PATTERNS = {
        'qwerty_row1': {'q': 'w', 'w': 'e', 'e': 'r', 'r': 't', 't': 'y', 
                       'y': 'u', 'u': 'i', 'i': 'o', 'o': 'p'},
        'qwerty_row2': {'a': 's', 's': 'd', 'd': 'f', 'f': 'g', 'g': 'h',
                       'h': 'j', 'j': 'k', 'k': 'l'},
        'qwerty_row3': {'z': 'x', 'x': 'c', 'c': 'v', 'v': 'b', 'b': 'n',
                       'n': 'm'},
        'number_row': {'1': '2', '2': '3', '3': '4', '4': '5', '5': '6',
                      '6': '7', '7': '8', '8': '9', '9': '0'}
    }
    
    def __init__(self, typing_style: Optional[TypingStyle] = None):
        self.typing_style = typing_style or random.choice(list(TypingStyle))
        self.emotional_state = HumanEmotion.NEUTRAL
        self.keystroke_history = deque(maxlen=100)
        self.error_rate = self._calculate_error_rate()
        self.current_wpm = self._calculate_wpm()
        self.typing_consistency = random.uniform(0.7, 0.95)
        
    def _calculate_error_rate(self) -> float:
        """Calculate typo rate based on typing style and emotion"""
        base_rate = {
            TypingStyle.TOUCH_TYPER: 0.05,
            TypingStyle.HYBRID: 0.08,
            TypingStyle.HUNT_AND_PECK: 0.15,
            TypingStyle.THUMB_TYPER: 0.12
        }[self.typing_style]
        
        # Emotional state modifiers
        emotion_modifiers = {
            HumanEmotion.NEUTRAL: 1.0,
            HumanEmotion.IMPATIENT: 1.5,
            HumanEmotion.CAREFUL: 0.6,
            HumanEmotion.DISTRACTED: 2.0,
            HumanEmotion.CONFUSED: 1.8,
            HumanEmotion.CONFIDENT: 0.8,
            HumanEmotion.TIRED: 1.3,
            HumanEmotion.FOCUSED: 0.7
        }
        
        return base_rate * emotion_modifiers.get(self.emotional_state, 1.0)
    
    def _calculate_wpm(self) -> int:
        """Calculate current typing speed based on style and emotion"""
        speed_data = self.TYPING_SPEEDS[self.typing_style]
        
        # Base speed with Gaussian distribution
        base_speed = int(np.random.normal(speed_data['mean'], speed_data['std']))
        base_speed = max(speed_data['min'], min(speed_data['max'], base_speed))
        
        # Emotional state modifiers
        emotion_modifiers = {
            HumanEmotion.NEUTRAL: 1.0,
            HumanEmotion.IMPATIENT: 1.2,
            HumanEmotion.CAREFUL: 0.8,
            HumanEmotion.DISTRACTED: 0.7,
            HumanEmotion.CONFUSED: 0.6,
            HumanEmotion.CONFIDENT: 1.1,
            HumanEmotion.TIRED: 0.75,
            HumanEmotion.FOCUSED: 1.15
        }
        
        return int(base_speed * emotion_modifiers.get(self.emotional_state, 1.0))
    
    def get_typing_delay(self, char: str, is_correction: bool = False) -> float:
        """
        Calculate realistic delay before typing a character
        Returns delay in seconds
        """
        # Base delay from WPM
        # WPM = characters per minute / 5 (average word length)
        chars_per_second = (self.current_wpm * 5) / 60
        base_delay = 1.0 / chars_per_second
        
        # Character-specific modifiers
        if char == ' ':
            modifier = random.uniform(0.8, 1.2)
        elif char in '.,!?;:':
            modifier = random.uniform(1.2, 1.8)  # Pause at punctuation
        elif char.isupper():
            modifier = random.uniform(1.5, 2.0)  # Shift key delay
        elif char.isdigit():
            modifier = random.uniform(1.1, 1.4)  # Numbers slightly slower
        else:
            modifier = random.uniform(0.9, 1.1)
        
        # Correction modifier (slower when correcting)
        if is_correction:
            modifier *= random.uniform(1.3, 1.8)
        
        # Emotional state modifier
        emotion_delay_modifiers = {
            HumanEmotion.IMPATIENT: 0.7,
            HumanEmotion.CAREFUL: 1.4,
            HumanEmotion.CONFUSED: 1.6,
            HumanEmotion.TIRED: 1.3,
            HumanEmotion.FOCUSED: 0.9
        }
        modifier *= emotion_delay_modifiers.get(self.emotional_state, 1.0)
        
        # Add random variance (humans aren't perfectly consistent)
        variance = random.gauss(1.0, 0.15)
        
        return base_delay * modifier * variance
    
    def get_dwell_time(self, char: str) -> float:
        """
        Calculate how long a key is held down
        Returns dwell time in seconds
        """
        if char == ' ':
            key_type = 'space'
        elif char == '\n' or char == '\r':
            key_type = 'enter'
        elif char == '\b' or char == '\x7f':
            key_type = 'backspace'
        elif char.isupper():
            key_type = 'shift'
        elif char.isdigit():
            key_type = 'number'
        elif char in '!@#$%^&*()_+-=[]{};\':",./<>?':
            key_type = 'symbol'
        elif char.isalpha():
            key_type = 'letter'
        else:
            key_type = 'function'
        
        dwell_range = self.DWELL_TIMES.get(key_type, (90, 140))
        dwell_ms = random.uniform(dwell_range[0], dwell_range[1])
        
        # Emotional state modifier
        emotion_modifiers = {
            HumanEmotion.IMPATIENT: 0.8,
            HumanEmotion.CAREFUL: 1.3,
            HumanEmotion.TIRED: 1.2,
            HumanEmotion.CONFIDENT: 0.9
        }
        dwell_ms *= emotion_modifiers.get(self.emotional_state, 1.0)
        
        return dwell_ms / 1000.0  # Convert to seconds
    
    def generate_typo(self, intended_char: str) -> Optional[str]:
        """
        Generate a realistic typo based on keyboard layout
        Returns typo character or None if no typo
        """
        if random.random() > self.error_rate:
            return None
        
        # Find which row the character is on
        typo_char = intended_char
        for row, patterns in self.TYPO_PATTERNS.items():
            if intended_char.lower() in patterns:
                # 70% chance of adjacent key, 30% chance of same finger different hand
                if random.random() < 0.7:
                    typo_char = patterns[intended_char.lower()]
                else:
                    # Pick random adjacent key
                    chars = list(patterns.keys())
                    idx = chars.index(intended_char.lower())
                    if idx > 0 and idx < len(chars) - 1:
                        typo_char = random.choice([chars[idx-1], chars[idx+1]])
                    elif idx == 0:
                        typo_char = chars[idx+1]
                    else:
                        typo_char = chars[idx-1]
                break
        
        # Preserve case
        if intended_char.isupper():
            typo_char = typo_char.upper()
        
        return typo_char if typo_char != intended_char else None
    
    def simulate_typing(self, text: str) -> List[TypingEvent]:
        """
        Simulate human typing of a complete text
        Returns list of typing events with timings
        """
        events = []
        current_time = 0.0
        correction_mode = False
        correction_buffer = []
        
        for i, char in enumerate(text):
            # Check for typo
            typo_char = self.generate_typo(char)
            
            if typo_char and not correction_mode:
                # Type wrong character
                events.append(TypingEvent(
                    key=typo_char,
                    timestamp=current_time,
                    dwell_time=self.get_dwell_time(typo_char),
                    flight_time=0.0,
                    error=True
                ))
                current_time += self.get_dwell_time(typo_char)
                
                # Pause after typo (realization time)
                current_time += random.uniform(0.2, 0.5)
                
                # Press backspace
                events.append(TypingEvent(
                    key='\b',
                    timestamp=current_time,
                    dwell_time=self.get_dwell_time('\b'),
                    flight_time=0.0,
                    error=False
                ))
                current_time += self.get_dwell_time('\b')
                
                # Pause before correction
                current_time += random.uniform(0.1, 0.3)
                
                # Type correct character
                events.append(TypingEvent(
                    key=char,
                    timestamp=current_time,
                    dwell_time=self.get_dwell_time(char),
                    flight_time=0.0,
                    error=False
                ))
                current_time += self.get_dwell_time(char)
                
            else:
                # Type correct character
                delay = self.get_typing_delay(char)
                current_time += delay
                
                events.append(TypingEvent(
                    key=char,
                    timestamp=current_time,
                    dwell_time=self.get_dwell_time(char),
                    flight_time=delay,
                    error=False
                ))
                
                # Occasionally pause mid-word (human hesitation)
                if random.random() < 0.05 and i < len(text) - 1:
                    current_time += random.uniform(0.1, 0.4)
            
            # Pause between words
            if char == ' ':
                current_time += random.uniform(0.05, 0.15)
            
            # Longer pause at sentence boundaries
            if char in '.!?' and i < len(text) - 1:
                current_time += random.uniform(0.3, 0.7)
        
        return events
    
    def set_emotional_state(self, emotion: HumanEmotion):
        """Update emotional state and recalculate behavior parameters"""
        self.emotional_state = emotion
        self.error_rate = self._calculate_error_rate()
        self.current_wpm = self._calculate_wpm()


class MouseBehaviorEngine:
    """
    Simulate human mouse movements with:
    - Bezier curve paths (humans don't move in straight lines)
    - Variable speed profiles (accelerate/decelerate)
    - Micro-jitter (hand tremor)
    - Overshoot and correction patterns
    - Misclicks (5-10% of clicks)
    """
    
    def __init__(self):
        self.movement_history = deque(maxlen=100)
        self.click_history = deque(maxlen=50)
        self.screen_width = 1920
        self.screen_height = 1080
        self.mouse_speed_factor = random.uniform(0.8, 1.2)
        self.tremor_intensity = random.uniform(0.1, 0.5)
        self.accuracy = random.uniform(0.85, 0.98)
        self.bezier = BezierCurveGenerator()
        
    def set_screen_dimensions(self, width: int, height: int):
        """Update screen dimensions for coordinate calculations"""
        self.screen_width = width
        self.screen_height = height
    
    async def move_to_element(
        self,
        element_x: int,
        element_y: int,
        start_x: Optional[int] = None,
        start_y: Optional[int] = None,
        emotion: HumanEmotion = HumanEmotion.NEUTRAL
    ) -> List[MouseMovement]:
        """
        Generate human-like mouse movement to an element
        """
        if start_x is None or start_y is None:
            # Start from random position (simulating mouse already somewhere)
            start_x = random.randint(0, self.screen_width)
            start_y = random.randint(0, self.screen_height)
        
        # Add human inaccuracy - don't go directly to element
        # Aim slightly off, then correct
        if random.random() > self.accuracy:
            element_x += random.randint(-20, 20)
            element_y += random.randint(-20, 20)
        
        # Generate Bezier curve path
        path_points = self.bezier.generate_bezier_path(
            start_x, start_y, element_x, element_y,
            num_points=random.randint(40, 80)
        )
        
        # Apply smoothing
        path_points = self.bezier.smooth_path(path_points, window_size=5)
        
        movements = []
        current_time = 0.0
        
        for i, (x, y, time_delta) in enumerate(path_points):
            # Apply emotional state modifiers
            emotion_speed_modifiers = {
                HumanEmotion.IMPATIENT: 1.5,
                HumanEmotion.CAREFUL: 0.6,
                HumanEmotion.TIRED: 0.7,
                HumanEmotion.CONFIDENT: 1.2,
                HumanEmotion.DISTRACTED: 0.8
            }
            
            speed_mod = emotion_speed_modifiers.get(emotion, 1.0)
            adjusted_delta = time_delta * self.mouse_speed_factor * speed_mod
            
            current_time += adjusted_delta
            
            # Calculate velocity and acceleration
            if i > 0:
                prev_x, prev_y, _ = path_points[i-1]
                distance = math.sqrt((x - prev_x)**2 + (y - prev_y)**2)
                velocity = distance / adjusted_delta if adjusted_delta > 0 else 0
                
                if i > 1:
                    prev_prev_x, prev_prev_y, _ = path_points[i-2]
                    prev_distance = math.sqrt((prev_x - prev_prev_x)**2 + (prev_y - prev_prev_y)**2)
                    prev_velocity = prev_distance / adjusted_delta if adjusted_delta > 0 else 0
                    acceleration = (velocity - prev_velocity) / adjusted_delta
                    
                    if i > 2:
                        # Calculate jerk (rate of change of acceleration)
                        prev_prev_distance = 0  # Simplified for brevity
                        jerk = 0
                    else:
                        jerk = 0
                else:
                    acceleration = 0
                    jerk = 0
            else:
                velocity = 0
                acceleration = 0
                jerk = 0
            
            movements.append(MouseMovement(
                x=x,
                y=y,
                timestamp=current_time,
                velocity=velocity,
                acceleration=acceleration,
                jerk=jerk
            ))
        
        return movements
    
    async def generate_click(
        self,
        x: int,
        y: int,
        button: str = 'left',
        emotion: HumanEmotion = HumanEmotion.NEUTRAL
    ) -> ClickEvent:
        """
        Generate a realistic click event with potential misclick
        """
        misclick = False
        click_x, click_y = x, y
        
        # Misclick probability based on emotion
        misclick_rates = {
            HumanEmotion.NEUTRAL: 0.05,
            HumanEmotion.IMPATIENT: 0.12,
            HumanEmotion.CAREFUL: 0.02,
            HumanEmotion.DISTRACTED: 0.15,
            HumanEmotion.TIRED: 0.10,
            HumanEmotion.CONFIDENT: 0.08
        }
        
        if random.random() < misclick_rates.get(emotion, 0.05):
            misclick = True
            # Misclick radius: 5-30 pixels
            radius = random.randint(5, 30)
            angle = random.uniform(0, 2 * math.pi)
            click_x = x + int(radius * math.cos(angle))
            click_y = y + int(radius * math.sin(angle))
            
            # Bound to screen
            click_x = max(0, min(self.screen_width, click_x))
            click_y = max(0, min(self.screen_height, click_y))
        
        # Click pressure (harder when impatient, softer when careful)
        pressure_modifiers = {
            HumanEmotion.IMPATIENT: 0.9,
            HumanEmotion.CAREFUL: 0.5,
            HumanEmotion.TIRED: 0.6,
            HumanEmotion.CONFIDENT: 0.8
        }
        
        base_pressure = random.uniform(0.6, 0.9)
        pressure = base_pressure * pressure_modifiers.get(emotion, 0.75)
        
        return ClickEvent(
            x=click_x,
            y=click_y,
            timestamp=time.time(),
            button=button,
            pressure=pressure,
            misclick=misclick
        )


class ScrollBehaviorEngine:
    """
    Simulate human scrolling patterns:
    - Variable scroll speed
    - Acceleration and deceleration
    - Pause-to-read behavior
    - Occasional back-scroll
    """
    
    def __init__(self):
        self.scroll_history = deque(maxlen=50)
        self.reading_speed_wpm = random.randint(200, 300)
        
    async def generate_scroll_sequence(
        self,
        total_distance: int,
        content_density: str = 'medium',  # 'low', 'medium', 'high'
        emotion: HumanEmotion = HumanEmotion.NEUTRAL
    ) -> List[ScrollEvent]:
        """
        Generate realistic scroll sequence for reading content
        """
        events = []
        current_y = 0
        current_time = 0.0
        
        # Scroll speed by content density (pixels per second)
        scroll_speeds = {
            'low': random.randint(800, 1200),
            'medium': random.randint(400, 700),
            'high': random.randint(150, 300)
        }
        
        base_speed = scroll_speeds.get(content_density, 500)
        
        # Emotional state modifiers
        emotion_speed_modifiers = {
            HumanEmotion.IMPATIENT: 1.5,
            HumanEmotion.CAREFUL: 0.7,
            HumanEmotion.TIRED: 0.6,
            HumanEmotion.DISTRACTED: 1.3,
            HumanEmotion.FOCUSED: 0.9
        }
        
        speed_modifier = emotion_speed_modifiers.get(emotion, 1.0)
        
        while current_y < total_distance:
            # Random scroll amount
            scroll_amount = random.randint(50, 150)
            if current_y + scroll_amount > total_distance:
                scroll_amount = total_distance - current_y
            
            # Calculate scroll speed with acceleration profile
            # Humans scroll faster at start, slower near bottom
            progress = current_y / total_distance
            speed_factor = 1.0 - (progress * 0.3)  # Slow down as we go
            
            scroll_speed = base_speed * speed_modifier * speed_factor
            scroll_duration = scroll_amount / scroll_speed
            
            # Add micro-pauses for reading
            if random.random() < 0.3:
                # Pause to read content
                read_time = self._calculate_read_time(scroll_amount, content_density)
                current_time += read_time
            
            events.append(ScrollEvent(
                delta_y=-scroll_amount,  # Negative for scroll down
                timestamp=current_time,
                speed=scroll_speed,
                acceleration=0,  # Simplified
                direction='down'
            ))
            
            current_time += scroll_duration
            current_y += scroll_amount
            
            # 10% chance to scroll back up slightly (re-reading)
            if random.random() < 0.1 and current_y > 200:
                back_amount = random.randint(30, 100)
                events.append(ScrollEvent(
                    delta_y=back_amount,
                    timestamp=current_time,
                    speed=scroll_speed * 0.8,
                    acceleration=0,
                    direction='up'
                ))
                current_time += scroll_duration * 0.5
                current_y -= back_amount
        
        return events
    
    def _calculate_read_time(self, scroll_amount: int, content_density: str) -> float:
        """Calculate time needed to read scrolled content"""
        # Approximate words per pixel based on content density
        words_per_pixel = {
            'low': 0.01,
            'medium': 0.02,
            'high': 0.04
        }
        
        words = scroll_amount * words_per_pixel.get(content_density, 0.02)
        read_time = (words / self.reading_speed_wpm) * 60  # Convert to seconds
        
        # Add variance
        read_time *= random.uniform(0.8, 1.5)
        
        return read_time


class FormFillingBehaviorEngine:
    """
    Simulate human form filling behavior:
    - Non-linear field order (humans jump around)
    - Pause to think before complex fields
    - Correction patterns
    - Field revisits
    """
    
    def __init__(self):
        self.typing_engine = TypingBehaviorEngine()
        self.mouse_engine = MouseBehaviorEngine()
        self.field_interaction_history = deque(maxlen=20)
        
    async def simulate_form_filling(
        self,
        form_fields: List[Dict[str, Any]],
        user_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Simulate human-like form filling with natural field order
        """
        interactions = {}
        field_order = self._generate_natural_field_order(form_fields)
        
        for field_name in field_order:
            field_data = next((f for f in form_fields if f['name'] == field_name), None)
            if not field_data or field_name not in user_data:
                continue
            
            # Pause before complex fields
            if field_data.get('type') in ['email', 'phone', 'password']:
                await asyncio.sleep(random.uniform(0.5, 1.5))
            else:
                await asyncio.sleep(random.uniform(0.1, 0.4))
            
            # Simulate clicking on field
            click_event = await self.mouse_engine.generate_click(
                x=field_data.get('x', 500),
                y=field_data.get('y', 300),
                button='left'
            )
            
            # Type the value with human-like behavior
            value = str(user_data[field_name])
            typing_events = self.typing_engine.simulate_typing(value)
            
            # 15% chance to revisit and correct a field
            if random.random() < 0.15 and len(interactions) > 2:
                revisit_field = random.choice(list(interactions.keys()))
                await asyncio.sleep(random.uniform(0.3, 0.8))
                # Re-type the value (partial correction)
                # Simplified for brevity
            
            interactions[field_name] = {
                'click': click_event,
                'typing_events': typing_events,
                'value': value,
                'timestamp': time.time()
            }
        
        return interactions
    
    def _generate_natural_field_order(self, form_fields: List[Dict[str, Any]]) -> List[str]:
        """
        Generate non-linear field order that mimics human behavior
        Humans don't always fill forms top-to-bottom
        """
        field_names = [f['name'] for f in form_fields]
        
        # Start with obvious fields
        order = []
        
        # Always do first name/last name first if present
        name_fields = [f for f in field_names if 'name' in f.lower()]
        for field in name_fields:
            if field not in order:
                order.append(field)
        
        # Email usually early
        if 'email' in field_names and 'email' not in order:
            order.append('email')
        
        # Add remaining fields in semi-random order
        remaining = [f for f in field_names if f not in order]
        random.shuffle(remaining)
        
        # But keep some logical grouping
        grouped_fields = []
        for field in remaining:
            if 'address' in field.lower():
                grouped_fields.insert(0, field)  # Address fields together
            elif 'phone' in field.lower():
                grouped_fields.append(field)
            elif 'password' in field.lower():
                grouped_fields.append(field)
            else:
                grouped_fields.append(field)
        
        order.extend(grouped_fields)
        
        return order


class GazeSimulationEngine:
    """
    Simulate eye tracking / visual attention
    Google's ML models can detect where users are looking
    """
    
    def __init__(self):
        self.gaze_points = deque(maxlen=100)
        self.attention_map = {}
        
    def generate_gaze_sequence(
        self,
        elements: List[Dict[str, Any]],
        duration: float = 10.0
    ) -> List[GazePoint]:
        """
        Generate realistic eye movement sequence
        Humans don't look at what they're clicking 100% of the time
        """
        gaze_events = []
        current_time = 0.0
        
        while current_time < duration:
            # 70% chance to look at current interaction area
            # 30% chance to look elsewhere (distracted)
            if random.random() < 0.7 and elements:
                target = random.choice(elements)
                x = target.get('x', 960)
                y = target.get('y', 540)
            else:
                # Look at random screen location
                x = random.randint(0, 1920)
                y = random.randint(0, 1080)
            
            # Humans fixate on points for 200-600ms
            gaze_duration = random.uniform(0.2, 0.6)
            
            gaze_events.append(GazePoint(
                x=x,
                y=y,
                timestamp=current_time,
                duration=gaze_duration
            ))
            
            current_time += gaze_duration
            
            # Saccade to next point (20-50ms)
            current_time += random.uniform(0.02, 0.05)
        
        return gaze_events


class HumanBehaviorPipeline:
    """
    Complete human behavior simulation pipeline
    Combines all behavioral engines into a single unified interface
    """
    
    def __init__(self):
        self.typing = TypingBehaviorEngine()
        self.mouse = MouseBehaviorEngine()
        self.scroll = ScrollBehaviorEngine()
        self.form = FormFillingBehaviorEngine()
        self.gaze = GazeSimulationEngine()
        
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.behavior_log = []
        self.current_emotion = HumanEmotion.NEUTRAL
        
    async def before_action(self, action_type: str, **kwargs):
        """
        Execute pre-action behavior (hesitation, preparation)
        """
        # Humans rarely act immediately
        hesitation_time = self._calculate_hesitation(action_type)
        await asyncio.sleep(hesitation_time)
        
        # Log behavior for ML training
        self.behavior_log.append({
            'timestamp': time.time(),
            'action': 'pre_' + action_type,
            'hesitation': hesitation_time,
            'emotion': self.current_emotion.value,
            **kwargs
        })
    
    async def after_action(self, action_type: str, **kwargs):
        """
        Execute post-action behavior (confirmation, double-check)
        """
        # Humans often pause after actions
        pause_time = self._calculate_post_action_pause(action_type)
        await asyncio.sleep(pause_time)
        
        self.behavior_log.append({
            'timestamp': time.time(),
            'action': 'post_' + action_type,
            'pause': pause_time,
            'emotion': self.current_emotion.value,
            **kwargs
        })
    
    def _calculate_hesitation(self, action_type: str) -> float:
        """Calculate hesitation time before action"""
        base_hesitation = {
            'click': random.uniform(0.1, 0.3),
            'type': random.uniform(0.05, 0.15),
            'scroll': random.uniform(0.1, 0.25),
            'submit': random.uniform(0.3, 0.8),
            'navigate': random.uniform(0.2, 0.5)
        }.get(action_type, 0.2)
        
        # Emotional modifiers
        emotion_modifiers = {
            HumanEmotion.IMPATIENT: 0.5,
            HumanEmotion.CAREFUL: 1.8,
            HumanEmotion.CONFUSED: 2.0,
            HumanEmotion.CONFIDENT: 0.7
        }
        
        return base_hesitation * emotion_modifiers.get(self.current_emotion, 1.0)
    
    def _calculate_post_action_pause(self, action_type: str) -> float:
        """Calculate pause time after action"""
        base_pause = {
            'click': random.uniform(0.05, 0.15),
            'type': random.uniform(0.02, 0.08),
            'scroll': random.uniform(0.1, 0.3),
            'submit': random.uniform(0.5, 1.5),
            'navigate': random.uniform(0.2, 0.4)
        }.get(action_type, 0.1)
        
        return base_pause
    
    def set_emotional_state(self, emotion: HumanEmotion):
        """Update emotional state across all engines"""
        self.current_emotion = emotion
        self.typing.set_emotional_state(emotion)
    
    def get_behavior_signature(self) -> Dict[str, Any]:
        """
        Generate unique behavior signature for this session
        Used to maintain consistent behavior across the entire account creation
        """
        return {
            'session_id': self.session_id,
            'typing_style': self.typing.typing_style.value,
            'typing_speed': self.typing.current_wpm,
            'error_rate': self.typing.error_rate,
            'mouse_speed': self.mouse.mouse_speed_factor,
            'mouse_accuracy': self.mouse.accuracy,
            'tremor_intensity': self.mouse.tremor_intensity,
            'reading_speed': self.scroll.reading_speed_wpm,
            'dominant_emotion': self.current_emotion.value,
            'behavior_count': len(self.behavior_log)
        }
    
    def export_behavior_log(self, filepath: str = None):
        """Export behavior log for analysis/debugging"""
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(self.behavior_log, f, indent=2)
        return self.behavior_log


# ============================================================================
# ASYNC HELPER FUNCTIONS FOR PLAYWRIGHT INTEGRATION
# ============================================================================

async def human_type(page, selector: str, text: str, behavior: HumanBehaviorPipeline = None):
    """
    Type text like a human with realistic delays and typos
    Drop-in replacement for Playwright's page.type()
    """
    if behavior is None:
        behavior = HumanBehaviorPipeline()
    
    # Find the element
    element = await page.wait_for_selector(selector)
    
    # Click on the element with human-like movement
    await behavior.before_action('click')
    box = await element.bounding_box()
    if box:
        # Generate human mouse movement
        movements = await behavior.mouse.move_to_element(
            box['x'] + box['width'] / 2,
            box['y'] + box['height'] / 2
        )
        # Replay movements (simplified - actual implementation would stream these)
        for move in movements:
            await page.mouse.move(move.x, move.y)
    
    await element.click()
    await behavior.after_action('click')
    
    # Type the text
    await behavior.before_action('type')
    typing_events = behavior.typing.simulate_typing(text)
    
    for event in typing_events:
        if event.key == '\b':
            await page.keyboard.press('Backspace')
        else:
            await page.keyboard.type(event.key)
        await asyncio.sleep(event.dwell_time)
    
    await behavior.after_action('type')


async def human_click(page, selector: str, behavior: HumanBehaviorPipeline = None):
    """
    Click like a human with curved mouse movement and potential misclicks
    """
    if behavior is None:
        behavior = HumanBehaviorPipeline()
    
    element = await page.wait_for_selector(selector)
    
    await behavior.before_action('click')
    
    box = await element.bounding_box()
    if box:
        target_x = box['x'] + box['width'] / 2
        target_y = box['y'] + box['height'] / 2
        
        # Generate human mouse movement
        movements = await behavior.mouse.move_to_element(
            target_x, target_y,
            emotion=behavior.current_emotion
        )
        
        # Stream movements with realistic timing
        for move in movements:
            await page.mouse.move(move.x, move.y)
            await asyncio.sleep(0.016)  # 60fps
        
        # Generate click with possible misclick
        click = await behavior.mouse.generate_click(
            target_x, target_y,
            emotion=behavior.current_emotion
        )
        
        if click.misclick:
            # Misclick - click wrong spot
            await page.mouse.click(click.x, click.y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            # Correct and click right spot
            await page.mouse.click(target_x, target_y)
        else:
            await page.mouse.click(target_x, target_y)
    
    await behavior.after_action('click')


async def human_scroll(page, selector: str = 'body', distance: int = 1000, 
                       behavior: HumanBehaviorPipeline = None):
    """
    Scroll like a human with variable speed and pauses
    """
    if behavior is None:
        behavior = HumanBehaviorPipeline()
    
    await behavior.before_action('scroll')
    
    scroll_events = await behavior.scroll.generate_scroll_sequence(
        distance,
        content_density='medium',
        emotion=behavior.current_emotion
    )
    
    for event in scroll_events:
        await page.mouse.wheel(0, event.delta_y)
        await asyncio.sleep(0.016)  # 60fps
    
    await behavior.after_action('scroll')


async def human_fill_form(page, form_data: Dict[str, str], 
                         field_mapping: Dict[str, str],
                         behavior: HumanBehaviorPipeline = None):
    """
    Complete form filling with human-like behavior
    """
    if behavior is None:
        behavior = HumanBehaviorPipeline()
    
    # Generate form fields from page
    form_fields = []
    for field_name, selector in field_mapping.items():
        try:
            element = await page.query_selector(selector)
            if element:
                box = await element.bounding_box()
                form_fields.append({
                    'name': field_name,
                    'selector': selector,
                    'x': box['x'] + box['width'] / 2 if box else 500,
                    'y': box['y'] + box['height'] / 2 if box else 300,
                    'type': await element.get_attribute('type') or 'text'
                })
        except:
            continue
    
    # Generate natural field order
    field_order = behavior.form._generate_natural_field_order(form_fields)
    
    # Fill fields in human-like order
    for field_name in field_order:
        if field_name in form_data:
            selector = field_mapping[field_name]
            await human_click(page, selector, behavior)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await human_type(page, selector, form_data[field_name], behavior)
            await asyncio.sleep(random.uniform(0.05, 0.15))


# ============================================================================
# EXPORT PUBLIC INTERFACE
# ============================================================================

__all__ = [
    'HumanEmotion',
    'TypingStyle',
    'HumanBehaviorPipeline',
    'TypingBehaviorEngine',
    'MouseBehaviorEngine',
    'ScrollBehaviorEngine',
    'FormFillingBehaviorEngine',
    'GazeSimulationEngine',
    'human_type',
    'human_click',
    'human_scroll',
    'human_fill_form',
    'BezierCurveGenerator'
]