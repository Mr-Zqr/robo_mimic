from common.path_config import PROJECT_ROOT

import pygame
from pygame.locals import *
from enum import IntEnum, unique

@unique
class JoystickButton(IntEnum):
    # Standard PlayStation/Xbox Layout
    A = 0      # PS: Cross(×), Xbox: A
    B = 1      # PS: Circle(○), Xbox: B
    X = 2      # PS: Square(□), Xbox: X
    Y = 3      # PS: Triangle(△), Xbox: Y
    L1 = 4     # Left Bumper (L1 on PS)
    R1 = 5     # Right Bumper (R1 on PS)
    SELECT = 6   # Select/Share button
    START = 7  # Start/Options button
    L3 = 8     # Left Stick Press
    R3 = 9     # Right Stick Press
    HOME = 10  # PS: PS FSMCommand, Xbox: Xbox FSMCommand
    UP = 11    # D-pad Up (if mapped as separate button)
    DOWN = 12  # D-pad Down
    LEFT = 13  # D-pad Left
    RIGHT = 14 # D-pad Right

class JoyStick:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            raise RuntimeError("No joystick connected!")
        
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        
        self.button_count = self.joystick.get_numbuttons()
        self.button_states = [False] * self.button_count  
        self.button_pressed = [False] * self.button_count  
        self.button_released = [False] * self.button_count 

        self.axis_count = self.joystick.get_numaxes()
        self.axis_states = [0.0] * self.axis_count
        
        self.hat_count = self.joystick.get_numhats()
        self.hat_states = [(0, 0)] * self.hat_count
        
        
    def update(self):
        """update joystick state"""
        pygame.event.pump()  
        
        self.button_released = [False] * self.button_count
        
        for i in range(self.button_count):
            current_state = self.joystick.get_button(i) == 1
            if self.button_states[i] and not current_state:
                self.button_released[i] = True
            self.button_states[i] = current_state

        for i in range(self.axis_count):
            self.axis_states[i] = self.joystick.get_axis(i)
        
        for i in range(self.hat_count):
            self.hat_states[i] = self.joystick.get_hat(i)

    def is_button_pressed(self, button_id):
        """detect button pressed"""
        if 0 <= button_id < self.button_count:
            return self.button_states[button_id]
        return False

    def is_button_released(self, button_id):
        """detect button released"""
        if 0 <= button_id < self.button_count:
            return self.button_released[button_id]
        return False

    def get_axis_value(self, axis_id):
        """get joystick axis value"""
        if 0 <= axis_id < self.axis_count:
            return self.axis_states[axis_id]
        return 0.0

    def get_hat_direction(self, hat_id=0):
        """get joystick hat direction"""
        if 0 <= hat_id < self.hat_count:
            return self.hat_states[hat_id]
        return (0, 0)

@unique
class KeyboardButton(IntEnum):
    # Keyboard mapping to match JoystickButton layout
    A = 0      # 'J' key
    B = 1      # 'K' key  
    X = 2      # 'U' key
    Y = 3      # 'I' key
    L1 = 4     # 'Q' key
    R1 = 5     # 'E' key
    SELECT = 6 # 'ESC' key
    START = 7  # 'SPACE' key
    L3 = 8     # 'F' key
    R3 = 9     # 'G' key
    HOME = 10  # 'H' key
    UP = 11    # Arrow Up
    DOWN = 12  # Arrow Down
    LEFT = 13  # Arrow Left
    RIGHT = 14 # Arrow Right

class Keyboard:
    def __init__(self):
        pygame.init()
        
        # Create a separate window for keyboard input to avoid MuJoCo key conflicts
        self.screen = pygame.display.set_mode((400, 300))
        pygame.display.set_caption("Robot Keyboard Controller - Keep this window focused!")
        
        # Keyboard button mapping to pygame keys
        self.key_mapping = {
            KeyboardButton.A: pygame.K_j,
            KeyboardButton.B: pygame.K_k,
            KeyboardButton.X: pygame.K_u,
            KeyboardButton.Y: pygame.K_i,
            KeyboardButton.L1: pygame.K_q,
            KeyboardButton.R1: pygame.K_e,
            KeyboardButton.SELECT: pygame.K_ESCAPE,
            KeyboardButton.START: pygame.K_SPACE,
            KeyboardButton.L3: pygame.K_f,
            KeyboardButton.R3: pygame.K_g,
            KeyboardButton.HOME: pygame.K_h,
            KeyboardButton.UP: pygame.K_UP,
            KeyboardButton.DOWN: pygame.K_DOWN,
            KeyboardButton.LEFT: pygame.K_LEFT,
            KeyboardButton.RIGHT: pygame.K_RIGHT,
        }
        
        # Button states tracking
        self.button_count = len(self.key_mapping)
        self.button_states = [False] * self.button_count
        self.button_pressed = [False] * self.button_count
        self.button_released = [False] * self.button_count

        # Axis simulation using WASD and arrow keys
        self.axis_count = 4  # Simulating 4 axes like joystick
        self.axis_states = [0.0] * self.axis_count
        
        # Axis key mappings for movement simulation
        self.axis_keys = {
            # Axis 0: Left stick horizontal (A/D keys)
            0: {'negative': pygame.K_a, 'positive': pygame.K_d},
            # Axis 1: Left stick vertical (W/S keys)  
            1: {'negative': pygame.K_w, 'positive': pygame.K_s},
            # Axis 2: Right stick horizontal (Left/Right arrows when Shift held)
            2: {'negative': pygame.K_LEFT, 'positive': pygame.K_RIGHT},
            # Axis 3: Right stick vertical (Up/Down arrows when Shift held)
            3: {'negative': pygame.K_UP, 'positive': pygame.K_DOWN},
        }
        
        print("Keyboard controller initialized!")
        print("🎮 KEYBOARD CONTROL WINDOW CREATED!")
        print("⚠️  IMPORTANT: Keep the 'Robot Keyboard Controller' window focused for input!")
        print("   (Not the MuJoCo window - that has its own shortcuts)")
        print("")
        print("Key mapping:")
        print("  Movement: WASD (left stick), Shift+Arrows (right stick)")
        print("  Actions: J(A), K(B), U(X), I(Y)")
        print("  Bumpers: Q(L1), E(R1)")
        print("  Special: Space(START), Esc(SELECT), F(L3), G(R3), H(HOME)")
        
        # Draw instructions on the control window
        self._draw_instructions()
    
    def _draw_instructions(self):
        """Draw control instructions on the pygame window"""
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)
        
        # Clear screen
        self.screen.fill((30, 30, 40))
        
        # Title
        title = font.render("Robot Keyboard Controller", True, (255, 255, 255))
        self.screen.blit(title, (10, 10))
        
        # Instructions
        instructions = [
            "Keep this window focused!",
            "",
            "Movement:",
            "  WASD - Move robot",
            "  Shift+Arrows - Rotate",
            "",
            "Actions:",
            "  J(A), K(B), U(X), I(Y)",
            "  Q(L1), E(R1) - Shoulders",
            "",
            "Special:",
            "  Space(START), Esc(EXIT)",
            "  F(L3), G(R3), H(HOME)"
        ]
        
        y_offset = 40
        for line in instructions:
            if line == "":
                y_offset += 5
                continue
            color = (255, 255, 0) if "Keep this window" in line else (200, 200, 200)
            text = small_font.render(line, True, color)
            self.screen.blit(text, (10, y_offset))
            y_offset += 18
        
        pygame.display.flip()
        
    def update(self):
        """Update keyboard state"""
        # Handle pygame events to keep window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Don't close, just minimize impact
                pass
        
        pygame.event.pump()
        
        # Reset button released states
        self.button_released = [False] * self.button_count
        
        # Get current keyboard state
        keys = pygame.key.get_pressed()
        shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        
        # Update button states
        for button_id, pygame_key in self.key_mapping.items():
            current_state = keys[pygame_key]
            
            # Check for button release
            if self.button_states[button_id] and not current_state:
                self.button_released[button_id] = True
                
            self.button_states[button_id] = current_state
        
        # Update axis states (simulate analog stick with digital keys)
        for axis_id, axis_mapping in self.axis_keys.items():
            negative_pressed = keys[axis_mapping['negative']]
            positive_pressed = keys[axis_mapping['positive']]
            
            # For axes 2 and 3 (right stick), require Shift key
            if axis_id >= 2 and not shift_pressed:
                self.axis_states[axis_id] = 0.0
                continue
                
            if negative_pressed and positive_pressed:
                self.axis_states[axis_id] = 0.0  # Both pressed, cancel out
            elif negative_pressed:
                self.axis_states[axis_id] = -1.0
            elif positive_pressed:
                self.axis_states[axis_id] = 1.0
            else:
                self.axis_states[axis_id] = 0.0
    
    def is_button_pressed(self, button_id):
        """Detect if button is currently pressed"""
        if 0 <= button_id < self.button_count:
            return self.button_states[button_id]
        return False
    
    def is_button_released(self, button_id):
        """Detect if button was just released"""
        if 0 <= button_id < self.button_count:
            return self.button_released[button_id]
        return False
    
    def get_axis_value(self, axis_id):
        """Get simulated axis value (-1.0 to 1.0)"""
        if 0 <= axis_id < self.axis_count:
            return self.axis_states[axis_id]
        return 0.0
    
    def get_hat_direction(self, hat_id=0):
        """Get D-pad direction (simulated using arrow keys without Shift)"""
        keys = pygame.key.get_pressed()
        shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        
        # Only use arrow keys as D-pad when Shift is NOT pressed
        if not shift_pressed:
            x = 0
            y = 0
            if keys[pygame.K_LEFT]:
                x = -1
            elif keys[pygame.K_RIGHT]:
                x = 1
            if keys[pygame.K_UP]:
                y = 1
            elif keys[pygame.K_DOWN]:
                y = -1
            return (x, y)
        return (0, 0)