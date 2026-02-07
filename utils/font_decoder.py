import io
import os
import re
import ddddocr
from fontTools.ttLib import TTFont
from PIL import Image, ImageFont, ImageDraw

class ZhihuFontDecoder:
    def __init__(self):
        # Initialize OCR once
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        self.font_map = {}
        
        # Debug directory
        self.debug_dir = os.path.join(os.getcwd(), 'logs', 'debug_fonts')
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir, exist_ok=True)

    def load_font(self, font_data):
        """
        Load font data and update the mapping table.
        Args:
            font_data (bytes): The binary data of the font file (woff/woff2).
        """
        try:
            # Load font from bytes
            font = TTFont(io.BytesIO(font_data))
            
            # Use a BytesIO object for PIL to load the font
            font_bytes_io = io.BytesIO(font_data)
            
            # Adopted User Parameters:
            # img_size = 128
            # font_size = int(img_size * 0.7) -> 89
            img_size = 128
            font_size = int(img_size * 0.7)
            
            try:
                pil_font = ImageFont.truetype(font_bytes_io, font_size)
            except Exception as e:
                print(f"Error loading font for rendering: {e}")
                return

            # Get the cmap table (character code to glyph index)
            cmap = font.getBestCmap()

            print(f"Loading font with {len(cmap)} characters...")

            for code_point, glyph_name in cmap.items():
                if not code_point:
                    continue
                    
                char = chr(code_point)
                
                # Render logic:
                image = Image.new("RGB", (img_size, img_size), (255, 255, 255))
                draw = ImageDraw.Draw(image)
                
                # Calculate text position to center it
                bbox = pil_font.getbbox(char)
                if bbox:
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (img_size - text_width) / 2 - bbox[0]
                    y = (img_size - text_height) / 2 - bbox[1]
                else:
                    x, y = 10, 10

                draw.text((x, y), char, font=pil_font, fill=(0, 0, 0))
                
                # Convert for OCR
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                # Save debug image
                debug_path = os.path.join(self.debug_dir, f"{hex(code_point)}.png")
                image.save(debug_path)
                
                # Perform OCR
                try:
                    res = self.ocr.classification(img_bytes)
                    
                    if res:
                        # Debug log for mapped characters
                        if res != char: # only log interesting mappings
                             print(f"Mapped {hex(code_point)} ({char}) -> {res}")
                        self.font_map[char] = res
                except Exception as e:
                    print(f"OCR failed for {hex(code_point)}: {e}")
            
            print(f"Font loaded. Total mappings: {len(self.font_map)}")
            print(f"Debug images saved to: {self.debug_dir}")

        except Exception as e:
            print(f"Error processing font data: {e}")

    def decode(self, text):
        """
        Replace obfuscated characters in text using the loaded font mapping.
        """
        if not self.font_map:
            return text
            
        decoded_text = []
        for char in text:
            if char in self.font_map:
                # print(f"Decoding: {char} -> {self.font_map[char]}")
                decoded_text.append(self.font_map[char])
            else:
                decoded_text.append(char)
        return "".join(decoded_text)
