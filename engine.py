"""
ZERX XIT - Sensitivity Engine
=============================
Core algorithm for generating Free Fire sensitivity values.
No random numbers. Every value is calculated from hardware + play style.
"""
import math

class SensitivityEngine:
    """Calculates optimal Free Fire sensitivity based on device hardware and play style."""

    # Play style multipliers (base sensitivity modifiers)
    STYLE_MODS = {
        'One Tap': {
            'general': 0.85, 'red_dot': 0.75, 'scope2x': 0.70, 'scope4x': 0.65,
            'sniper': 0.55, 'free_look': 0.80, 'dpi_mod': 1.10,
            'desc': 'Precision-focused. Lower sensitivity for headshots.'
        },
        'Balanced': {
            'general': 1.00, 'red_dot': 1.00, 'scope2x': 1.00, 'scope4x': 1.00,
            'sniper': 1.00, 'free_look': 1.00, 'dpi_mod': 1.00,
            'desc': 'Well-rounded settings for all situations.'
        },
        'Rusher': {
            'general': 1.20, 'red_dot': 1.15, 'scope2x': 1.10, 'scope4x': 1.05,
            'sniper': 0.90, 'free_look': 1.20, 'dpi_mod': 0.95,
            'desc': 'High mobility. Faster turning and close-range combat.'
        },
        'Freestyle': {
            'general': 1.10, 'red_dot': 1.05, 'scope2x': 1.00, 'scope4x': 0.95,
            'sniper': 0.85, 'free_look': 1.15, 'dpi_mod': 1.05,
            'desc': 'Adaptive play. Medium-high with smooth transitions.'
        },
        'Sniper': {
            'general': 0.75, 'red_dot': 0.65, 'scope2x': 0.60, 'scope4x': 0.55,
            'sniper': 0.45, 'free_look': 0.70, 'dpi_mod': 1.20,
            'desc': 'Long-range specialist. Ultra-precise tracking.'
        },
        'Instaplayer': {
            'general': 1.30, 'red_dot': 1.25, 'scope2x': 1.20, 'scope4x': 1.10,
            'sniper': 1.00, 'free_look': 1.30, 'dpi_mod': 0.90,
            'desc': 'Maximum speed. For experienced players only.'
        }
    }

    # Processor tier scores (influence on base sensitivity)
    PROC_TIERS = {
        # Flagship
        'Snapdragon 8 Gen 3': 100, 'A17 Pro': 100, 'Tensor G3': 95,
        'Snapdragon 8 Gen 2': 95, 'A16 Bionic': 95, 'Dimensity 9200+': 94,
        'Snapdragon 8+ Gen 1': 92, 'Kirin 9010': 92, 'Dimensity 9000+': 91,
        'Snapdragon 8s Gen 3': 93, 'Snapdragon 8s Gen 2': 90,
        # Upper mid
        'Snapdragon 7+ Gen 3': 85, 'Dimensity 8200': 84, 'Snapdragon 7 Gen 3': 82,
        'Dimensity 7200': 80, 'Dimensity 7200 Pro': 81, 'Snapdragon 7s Gen 2': 78,
        'Tensor G2': 80, 'A15 Bionic': 88, 'Kirin 9000S': 87,
        # Mid
        'Snapdragon 778G': 72, 'Snapdragon 778G+': 74, 'Dimensity 7050': 70,
        'Dimensity 7020': 68, 'Dimensity 6080': 65, 'Snapdragon 695': 64,
        'Snapdragon 685': 60, 'Snapdragon 680': 58, 'Helio G99': 62,
        'Exynos 1580': 75, 'Exynos 1480': 72, 'Exynos 1380': 68,
        # Lower mid
        'Helio G85': 55, 'Helio G88': 56, 'Snapdragon 480+': 52,
        'Dimensity 6020': 58, 'Dimensity 6100+': 56, 'Unisoc T616': 48,
        'Exynos 1280': 60,
        # Entry
        'Helio G36': 40, 'Helio G37': 42, 'Unisoc T606': 38,
        'Unisoc T603': 35, 'Unisoc SC9863A': 30, 'Snapdragon 4 Gen 1': 50,
        'Dimensity 700': 52, 'PowerVR GE8320': 28, 'PowerVR GE8322': 30,
        'Mali-G52': 45, 'Mali-G57': 50
    }

    # Refresh rate impact
    REFRESH_MODS = {
        '144Hz': 1.08, '120Hz': 1.05, '90Hz': 1.02, '60Hz': 1.00,
        '165Hz': 1.10, '240Hz': 1.12
    }

    # RAM impact (smoothing factor)
    RAM_MODS = {
        '24GB': 1.06, '16GB': 1.05, '12GB': 1.04, '8GB': 1.02,
        '6GB': 1.00, '4GB': 0.97, '3GB': 0.94, '2GB': 0.90
    }

    def _get_proc_score(self, processor):
        """Get processor performance score."""
        if not processor or processor == 'Unknown':
            return 50
        # Try exact match first
        if processor in self.PROC_TIERS:
            return self.PROC_TIERS[processor]
        # Try partial match
        for name, score in self.PROC_TIERS.items():
            if name.lower() in processor.lower() or processor.lower() in name.lower():
                return score
        return 50

    def _get_refresh_mod(self, refresh_rate):
        """Get refresh rate modifier."""
        if not refresh_rate:
            return 1.0
        rr = str(refresh_rate).replace('Hz', '').strip()
        key = f"{rr}Hz"
        return self.REFRESH_MODS.get(key, 1.0)

    def _get_ram_mod(self, ram):
        """Get RAM modifier."""
        if not ram:
            return 1.0
        r = str(ram).replace('GB', '').strip()
        key = f"{r}GB"
        return self.RAM_MODS.get(key, 1.0)

    # Screen-size correction: larger, denser panels need a slightly lower
    # multiplier because the same swipe covers more physical distance.
    def _screen_factor(self, screen):
        if not screen:
            return 1.0, None
        try:
            width = float(screen.get('width') or 0)
            height = float(screen.get('height') or 0)
            ratio = float(screen.get('pixel_ratio') or 1) or 1
        except (TypeError, ValueError):
            return 1.0, None
        if width <= 0 or height <= 0:
            return 1.0, None
        # CSS pixels -> approximate physical pixels
        long_edge = max(width, height) * ratio
        if long_edge <= 0:
            return 1.0, None
        # 2400px long edge is the reference panel
        factor = (2400 / long_edge) ** 0.25
        factor = max(0.92, min(1.08, factor))
        return factor, round(long_edge)

    def _calculate_base(self, device_info, play_style):
        """Calculate base sensitivity values from hardware."""
        proc = device_info.get('processor', 'Unknown')
        ram = device_info.get('ram', '4GB')
        refresh = device_info.get('refresh_rate', '60Hz')
        perf_score = device_info.get('performance_score', 50)
        gaming_score = device_info.get('gaming_score', 50)

        proc_score = self._get_proc_score(proc)
        ram_mod = self._get_ram_mod(ram)
        refresh_mod = self._get_refresh_mod(refresh)

        # Hardware capability factor (0.8 to 1.2)
        hw_factor = ((proc_score + perf_score + gaming_score) / 300) * 0.4 + 0.8
        hw_factor = max(0.75, min(1.25, hw_factor))

        # Combined modifier
        combined = hw_factor * ram_mod * refresh_mod

        # Base values (Free Fire typical ranges)
        bases = {
            'general': 85,
            'red_dot': 90,
            'scope2x': 75,
            'scope4x': 65,
            'sniper': 50,
            'free_look': 70,
            'dpi': 400
        }

        style = self.STYLE_MODS.get(play_style, self.STYLE_MODS['Balanced'])

        result = {}
        for key in bases:
            if key == 'dpi':
                result[key] = int(bases[key] * combined * style['dpi_mod'])
            else:
                result[key] = int(bases[key] * combined * style.get(key, 1.0))
            # Clamp to valid ranges
            if key == 'dpi':
                result[key] = max(200, min(1200, result[key]))
            else:
                result[key] = max(10, min(100, result[key]))

        return result, style['desc']

    def generate(self, device_info, play_style, vip=False, tune=0, screen=None):
        """Generate a complete sensitivity profile.

        tune   : -3..+3 manual adjustment steps (each step is 4%).
        screen : optional {'width', 'height', 'pixel_ratio'} reported by the browser.
        """
        base, desc = self._calculate_base(device_info, play_style)

        try:
            tune = int(tune)
        except (TypeError, ValueError):
            tune = 0
        tune = max(-3, min(3, tune))

        screen_factor, long_edge = self._screen_factor(screen)
        tune_factor = 1 + (tune * 0.04)

        for key in base:
            adjusted = base[key] * screen_factor * tune_factor
            if key == 'dpi':
                base[key] = max(200, min(1200, int(adjusted)))
            else:
                base[key] = max(10, min(100, int(adjusted)))

        notes = []
        if long_edge:
            notes.append(f"Screen calibration applied for a {long_edge}px panel.")
        if tune:
            notes.append(f"Manual adjustment: {tune:+d} step(s) ({tune * 4:+d}%).")
        if vip:
            notes.append('VIP profile: extended optimization guidance included.')

        return {
            'general': base['general'],
            'red_dot': base['red_dot'],
            'scope2x': base['scope2x'],
            'scope4x': base['scope4x'],
            'sniper': base['sniper'],
            'free_look': base['free_look'],
            'dpi': base['dpi'],
            'tune': tune,
            'screen_factor': round(screen_factor, 3),
            'notes': notes,
            'play_style_desc': desc,
            'device_summary': f"{device_info.get('brand', 'Unknown')} {device_info.get('model', 'Unknown')}",
            'optimization_score': self._calc_opt_score(device_info)
        }

    def _calc_opt_score(self, device_info):
        """Calculate an optimization score 0-100."""
        proc_score = self._get_proc_score(device_info.get('processor', ''))
        ram_mod = self._get_ram_mod(device_info.get('ram', ''))
        refresh_mod = self._get_refresh_mod(device_info.get('refresh_rate', ''))
        perf = device_info.get('performance_score', 50)
        gaming = device_info.get('gaming_score', 50)

        score = (proc_score * 0.3 + perf * 0.2 + gaming * 0.2 + 
                 (ram_mod * 50) * 0.15 + (refresh_mod * 50) * 0.15)
        return int(min(100, score))

    def fallback_tips(self, device_info, play_style, vip=False):
        """Generate fallback optimization tips when AI is unavailable."""
        proc = device_info.get('processor', 'Unknown')
        ram = device_info.get('ram', '4GB')
        refresh = device_info.get('refresh_rate', '60Hz')

        tips = {
            'phone_settings': [
                'Enable Game Mode / Performance Mode in phone settings',
                'Set screen refresh rate to maximum available',
                'Disable battery saver while gaming',
                'Clear background apps before playing'
            ],
            'developer_options': [
                'Enable Force GPU Rendering',
                'Disable HW overlays for better performance',
                'Set Background process limit to 2',
                'Enable Disable HW Overlays'
            ],
            'gaming_tips': [
                f'Play style: {play_style}. Practice in Training Ground first.',
                'Use gyroscope for better precision in long-range fights',
                'Adjust crosshair placement to head level',
                'Pre-aim corners before peeking'
            ],
            'optimization_tips': [
                f'Device detected: {proc} with {ram} RAM',
                f'Screen refresh: {refresh}. Enable highest setting.',
                'Close all apps before launching Free Fire',
                'Use stable WiFi or 4G/5G for lowest ping'
            ],
            'battery_tips': [
                'Lower screen brightness to 60-70%',
                'Disable vibration and haptic feedback',
                'Use original charger to prevent thermal throttling',
                'Play in cool environment when possible'
            ],
            'performance_tips': [
                'Set Free Fire graphics to Smooth + Ultra FPS',
                'Disable shadows and anti-aliasing',
                'Reduce character render distance if lag occurs',
                'Keep at least 5GB free storage on device'
            ],
            'sensitivity_advice': [
                'Your DPI is calibrated to your hardware profile',
                'If overshooting targets, reduce general sensitivity by 5',
                'If undershooting targets, increase red dot by 3-5',
                'Test in training ground for 10 minutes before ranked'
            ]
        }

        if vip:
            tips['advanced'] = [
                'Set Animation scales to 0.5x in Developer Options for a faster UI',
                'Force 4x MSAA only on flagship hardware; disable it on budget chipsets',
                'Enable the manufacturer game mode (Game Booster / Game Space / Panel)',
                'Charge to 80% before a long session to limit thermal throttling'
            ]

        return tips
