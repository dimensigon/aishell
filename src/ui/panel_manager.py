"""
Dynamic Panel Manager

Manages flexible panel sizing with content-aware priority.
"""

from typing import Dict
from dataclasses import dataclass


@dataclass
class PanelDimensions:
    """Panel dimension specification"""
    min: int
    max: int
    preferred: int


class DynamicPanelManager:
    """
    Manages dynamic panel sizing based on content and user activity.

    Features:
    - Content-aware sizing
    - Typing state detection
    - Priority-based allocation
    """

    def __init__(self):
        self.panel_weights = {
            'output': 0.5,
            'module': 0.3,
            'prompt': 0.2
        }
        self.active_typing = False
        self.content_sizes = {}

    def calculate_dimensions(self, terminal_height: int) -> Dict[str, PanelDimensions]:
        """
        Dynamically calculate panel dimensions.

        Args:
            terminal_height: Available terminal height

        Returns:
            Dictionary of panel dimensions
        """
        if self.active_typing:
            # Prioritize prompt when user is typing
            prompt_lines = self._calculate_prompt_lines()
            prompt_height = min(prompt_lines + 2, terminal_height // 2)

            remaining = terminal_height - prompt_height
            output_height = int(remaining * 0.7)
            module_height = remaining - output_height
        else:
            # Balance based on content
            output_content = self.content_sizes.get('output', 10)
            module_content = self.content_sizes.get('module', 5)

            total_content = output_content + module_content + 3

            if total_content <= terminal_height:
                # All content fits
                return {
                    'output': PanelDimensions(
                        min=output_content,
                        max=output_content,
                        preferred=output_content
                    ),
                    'module': PanelDimensions(
                        min=module_content,
                        max=module_content,
                        preferred=module_content
                    ),
                    'prompt': PanelDimensions(
                        min=3,
                        max=3,
                        preferred=3
                    )
                }
            else:
                # Apply weighted distribution
                output_height = int(terminal_height * self.panel_weights['output'])
                module_height = int(terminal_height * self.panel_weights['module'])
                prompt_height = terminal_height - output_height - module_height

        return {
            'output': PanelDimensions(
                min=output_height,
                max=output_height,
                preferred=output_height
            ),
            'module': PanelDimensions(
                min=module_height,
                max=module_height,
                preferred=module_height
            ),
            'prompt': PanelDimensions(
                min=prompt_height,
                max=terminal_height // 2,
                preferred=prompt_height
            )
        }

    def _calculate_prompt_lines(self) -> int:
        """Calculate required prompt lines"""
        # Placeholder - will be enhanced with actual prompt content
        return self.content_sizes.get('prompt', 1)

    def set_typing_state(self, is_typing: bool) -> None:
        """Update typing state"""
        self.active_typing = is_typing

    def update_content_size(self, panel: str, lines: int) -> None:
        """Update content size for a panel"""
        self.content_sizes[panel] = lines
