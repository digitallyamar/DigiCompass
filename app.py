import math
import tkinter as tk
from tkinter import ttk

def calculate_heading(raw_x, raw_y, raw_z, range_gauss=2):
    """
    Calculate 3D compass heading from QMC5883L raw magnetometer X, Y, Z values.
    
    Args:
        raw_x (int): Raw X-axis value (±12000 for ±2G, ±24000 for ±8G).
        raw_y (int): Raw Y-axis value (same limits).
        raw_z (int): Raw Z-axis value (same limits).
        range_gauss (int): Full-scale range in Gauss (2 for ±2G, 8 for ±8G).
    
    Returns:
        float: Heading in degrees (0 = North, 90 = East, 180 = South, 270 = West).
        str: Friendly direction (e.g., "North", "Northeast").
    
    Raises:
        ValueError: If raw values exceed range limits or all are zero.
    """
    # Set sensitivity and max raw value
    if range_gauss == 2:
        sensitivity = 12000  # ±2 Gauss mode
        max_raw = 12000
    elif range_gauss == 8:
        sensitivity = 3000   # ±8 Gauss mode
        max_raw = 24000
    else:
        raise ValueError("range_gauss must be 2 or 8")
    
    # Validate raw values
    for value, name in [(raw_x, "X"), (raw_y, "Y"), (raw_z, "Z")]:
        if not (-max_raw <= value <= max_raw):
            raise ValueError(f"Raw {name} must be between {-max_raw} and {max_raw} for ±{range_gauss}G mode")
    
    # Check for zero vector
    if raw_x == 0 and raw_y == 0 and raw_z == 0:
        raise ValueError("All raw values are zero; no heading can be calculated")
    
    # Convert raw to Gauss
    mag_x = raw_x / sensitivity
    mag_y = raw_y / sensitivity
    mag_z = raw_z / sensitivity
    
    # For 3D heading, project magnetic vector onto XY plane
    # Without accelerometer, we assume Z influences the field but heading is XY-based
    # Normalize to avoid Z dominating, but keep it simple
    # Heading = atan2(Y, X) adjusted for Z's contribution
    # If Z is large (e.g., vertical field), heading becomes less defined
    if mag_x == 0 and mag_y == 0:
        # Pure Z field (e.g., 0, 0, 12000): heading is undefined
        heading_degrees = 0  # Default to North, but could be any angle
        friendly_direction = "Undefined (vertical field)"
    else:
        # Calculate heading using X and Y, Z affects magnitude but not angle directly
        heading_radians = math.atan2(mag_y, mag_x)
        heading_degrees = heading_radians * (180 / math.pi)
        heading_degrees = heading_degrees % 360
        
        # Map to friendly direction
        directions = [
            "North", "Northeast", "East", "Southeast",
            "South", "Southwest", "West", "Northwest", "North"
        ]
        index = round(heading_degrees / 45) % 8
        friendly_direction = directions[index]
    
    return heading_degrees, friendly_direction

class MagnetometerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("QMC5883L 3D Compass")
        
        # Create input fields
        tk.Label(root, text="Raw X:").grid(row=0, column=0, padx=5, pady=5)
        self.x_entry = tk.Entry(root)
        self.x_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(root, text="Raw Y:").grid(row=1, column=0, padx=5, pady=5)
        self.y_entry = tk.Entry(root)
        self.y_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(root, text="Raw Z:").grid(row=2, column=0, padx=5, pady=5)
        self.z_entry = tk.Entry(root)
        self.z_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Range selection
        tk.Label(root, text="Range (±Gauss):").grid(row=3, column=0, padx=5, pady=5)
        self.range_var = tk.StringVar(value="2")
        range_menu = ttk.Combobox(root, textvariable=self.range_var, values=["2", "8"], state="readonly")
        range_menu.grid(row=3, column=1, padx=5, pady=5)
        
        # Range-specific label
        self.range_label = tk.Label(root, text="Valid range: -12000 to +12000 (±2G)")
        self.range_label.grid(row=4, column=0, columnspan=2, pady=5)
        range_menu.bind("<<ComboboxSelected>>", self.update_range_label)
        
        # Calculate button
        self.calculate_button = tk.Button(root, text="Calculate Direction", command=self.show_direction)
        self.calculate_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Result display
        self.result_label = tk.Label(root, text="Direction: Not calculated yet")
        self.result_label.grid(row=6, column=0, columnspan=2, pady=5)
        
        # Compass canvas
        self.canvas = tk.Canvas(root, width=100, height=100, bg="white")
        self.canvas.grid(row=0, column=2, rowspan=7, padx=10)
        self.canvas.create_oval(10, 10, 90, 90, outline="black")  # Compass circle
        self.needle = self.canvas.create_line(50, 50, 50, 20, fill="red", width=2)  # Needle (default North)
    
    def update_range_label(self, event=None):
        range_gauss = int(self.range_var.get())
        max_raw = 12000 if range_gauss == 2 else 24000
        self.range_label.config(text=f"Valid range: -{max_raw} to +{max_raw} (±{range_gauss}G)")
    
    def show_direction(self):
        try:
            # Get inputs
            raw_x = int(self.x_entry.get())
            raw_y = int(self.y_entry.get())
            raw_z = int(self.z_entry.get())
            range_gauss = int(self.range_var.get())
            
            # Calculate heading
            degrees, direction = calculate_heading(raw_x, raw_y, raw_z, range_gauss)
            
            # Update result
            self.result_label.config(text=f"Direction: {direction} ({degrees:.1f}°)")
            
            # Update compass needle
            self.canvas.delete(self.needle)
            rad = -degrees * (math.pi / 180)  # Convert to radians, negate for clockwise
            x2 = 50 + 30 * math.cos(rad)      # Needle length = 30
            y2 = 50 + 30 * math.sin(rad)
            self.needle = self.canvas.create_line(50, 50, x2, y2, fill="red", width=2)
        except ValueError as e:
            self.result_label.config(text=f"Error: {str(e)}")
            self.canvas.delete(self.needle)
            self.needle = self.canvas.create_line(50, 50, 50, 20, fill="red", width=2)  # Reset needle

if __name__ == "__main__":
    # Example usage without GUI
    raw_x, raw_y, raw_z = 6000, 0, 0  # Example: North in ±2G
    try:
        degrees, direction = calculate_heading(raw_x, raw_y, raw_z, range_gauss=2)
        print(f"Heading: {degrees:.1f} degrees, Direction: {direction}")
    except ValueError as e:
        print(f"Error: {e}")
    
    # Run GUI
    root = tk.Tk()
    app = MagnetometerGUI(root)
    root.mainloop()