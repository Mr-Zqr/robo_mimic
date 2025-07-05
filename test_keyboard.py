#!/usr/bin/env python3
"""
Test script for keyboard controller
Run this to test the keyboard input functionality
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.absolute()))

from common.joystick import Keyboard, KeyboardButton
import pygame
import time

def test_keyboard():
    print("Testing Keyboard Controller...")
    print("A separate control window will open.")
    print("Use the following keys in the control window:")
    print("  Movement: WASD (left stick), Shift+Arrows (right stick)")
    print("  Actions: J(A), K(B), U(X), I(Y)")
    print("  Bumpers: Q(L1), E(R1)")
    print("  Special: Space(START), Esc(SELECT), F(L3), G(R3), H(HOME)")
    print("Press ESC to exit")
    print("-" * 50)
    
    # Initialize keyboard controller (this will create the control window)
    keyboard = Keyboard()
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update keyboard state
        keyboard.update()
        
        # Check for exit condition
        if keyboard.is_button_pressed(KeyboardButton.SELECT):
            running = False
        
        # Print button states when pressed
        button_names = {
            KeyboardButton.A: "A(J)",
            KeyboardButton.B: "B(K)", 
            KeyboardButton.X: "X(U)",
            KeyboardButton.Y: "Y(I)",
            KeyboardButton.L1: "L1(Q)",
            KeyboardButton.R1: "R1(E)",
            KeyboardButton.START: "START(Space)",
            KeyboardButton.L3: "L3(F)",
            KeyboardButton.R3: "R3(G)",
            KeyboardButton.HOME: "HOME(H)",
        }
        
        # Check for button releases and print them
        for button_id, name in button_names.items():
            if keyboard.is_button_released(button_id):
                print(f"Button Released: {name}")
        
        # Print axis values when they change
        axis_values = [
            keyboard.get_axis_value(0),  # Left stick X
            keyboard.get_axis_value(1),  # Left stick Y
            keyboard.get_axis_value(2),  # Right stick X
            keyboard.get_axis_value(3),  # Right stick Y
        ]
        
        # Only print if any axis is non-zero
        if any(abs(val) > 0.1 for val in axis_values):
            print(f"Axes: Left({axis_values[0]:.1f}, {axis_values[1]:.1f}) " +
                  f"Right({axis_values[2]:.1f}, {axis_values[3]:.1f})")
        
        # Control the loop rate
        clock.tick(60)  # 60 FPS
        
    pygame.quit()
    print("Test completed!")

if __name__ == "__main__":
    test_keyboard()
