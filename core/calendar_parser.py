import fitz  # PyMuPDF
import os
import pandas as pd
import re
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from helper.resource_path import resource_path
from model.inference import CalendarDetector
from pdf2image import convert_from_path

poppler_path = resource_path("poppler-25.07.0\\Library\\bin")

class CalendarParser:
    """
    Uses YOLO for cell detection and PyMuPDF for text extraction
    Handles missing date columns automatically
    """
    
    def __init__(self, pdf_path, output_dir):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "pages")
        os.makedirs(self.images_dir, exist_ok=True)

    def run_yolo_detection(self):
        """Run YOLO to get cell boundaries"""
        pages = convert_from_path(self.pdf_path, dpi=300, poppler_path=poppler_path)
        image_paths = []
        for i, page in enumerate(pages):
            path = os.path.join(self.images_dir, f"page_{i+1}.jpg")
            page.save(path, "JPEG")
            image_paths.append(path)
        
        detector = CalendarDetector()
        detector.detect(self.images_dir, self.output_dir)
        
        return len(pages)

    def get_detections_for_page(self, page_num):
        """Load YOLO detections"""
        labels_path = os.path.join(self.output_dir, "calendar_detect", "labels", f"page_{page_num}.txt")
        
        if not os.path.exists(labels_path):
            return []
        
        detections = []
        with open(labels_path, "r") as f:
            for line in f:
                cls, x_center, y_center, width, height = map(float, line.split())
                detections.append({
                    "class": int(cls),
                    "x_center": x_center,
                    "y_center": y_center,
                    "width": width,
                    "height": height
                })
        return detections

    def yolo_to_bbox(self, detection, page_width, page_height):
        """Convert YOLO normalized coords to bounding box"""
        x_center = detection["x_center"] * page_width
        y_center = detection["y_center"] * page_height
        width = detection["width"] * page_width
        height = detection["height"] * page_height
        
        x0 = x_center - width / 2
        y0 = y_center - height / 2
        x1 = x_center + width / 2
        y1 = y_center + height / 2
        
        return (x0, y0, x1, y1)
    
    def get_nearest_date_row(self, row_y, date_rows):
        """
        Find the nearest date row above the given row_y position.
        date_rows: list of detected date rows for this page
        """
        candidates = [d for d in date_rows if d["y_center"] < row_y]
        if not candidates:
            return None
        return max(candidates, key=lambda d: d["y_center"])


    def extract_text_from_bbox(self, page, bbox):
        """Extract text from PDF within a bounding box"""
        x0, y0, x1, y1 = bbox
        rect = fitz.Rect(x0, y0, x1, y1)
        text = page.get_text("text", clip=rect)
        return " ".join(text.split()).strip()

    def build_grid(self, detections, page_width, page_height):
        """Build grid using row boundaries"""
        rows_det = [d for d in detections if d["class"] == 0]
        cells = [d for d in detections if d["class"] == 1]
        
        if not rows_det or not cells:
            return []
        
        # Add bbox and centers to all
        for cell in cells:
            bbox = self.yolo_to_bbox(cell, page_width, page_height)
            cell["bbox"] = bbox
            cell["center_y"] = (bbox[1] + bbox[3]) / 2
            cell["center_x"] = (bbox[0] + bbox[2]) / 2
        
        for row in rows_det:
            bbox = self.yolo_to_bbox(row, page_width, page_height)
            row["y_min"] = bbox[1]
            row["y_max"] = bbox[3]
            row["center_y"] = (bbox[1] + bbox[3]) / 2
        
        # Sort rows top to bottom
        rows_det.sort(key=lambda x: x["center_y"])
        
        # Assign cells to rows
        grid = []
        for row_det in rows_det:
            y_min = row_det["y_min"]
            y_max = row_det["y_max"]
            
            row_cells = [c for c in cells if y_min <= c["center_y"] <= y_max]
            row_cells.sort(key=lambda x: x["center_x"])
            
            if row_cells:
                grid.append(row_cells)
        
        return grid

    def extract_class_level(self, page):
        """Extract class level from page header"""
        rect = fitz.Rect(0, 0, page.rect.width, page.rect.height * 0.25)
        text = page.get_text("text", clip=rect).lower()
        
        patterns = [
            r"niveau\s*[:\s]+([a-z0-9\-]+)",
            r"\b(l[1-3][a-z]*)\b",
            r"\b(m[1-2][a-z]*)\b",
            r"\b(2i[a-z]*)\b",
        ]
        
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                return match.group(1).upper().replace(" ", "")
        
        return "UNKNOWN"

    def parse_page(self, doc, page_num):
        """Parse a single page with column alignment"""
        page = doc[page_num - 1]
        page_width = page.rect.width
        page_height = page.rect.height
        
        print(f"\n   Processing page {page_num}...")
        
        class_level = self.extract_class_level(page)
        print(f"   Class level: {class_level}")
        
        detections = self.get_detections_for_page(page_num)
        if not detections:
            print("   ⚠️  No detections")
            return []
        
        grid = self.build_grid(detections, page_width, page_height)
        
        if len(grid) < 3:
            print(f"   ⚠️  Only {len(grid)} rows")
            return []
        
        # Step 1: detect all date rows
        date_rows = []
        for row_cells in grid:
            row_texts = [self.extract_text_from_bbox(page, c["bbox"]) for c in row_cells]
            if any(re.search(r'\d{2}/\d{2}', t) for t in row_texts):
                date_rows.append({
                    "row_cells": row_cells,
                    "y_center": sum((c["center_y"] for c in row_cells)) / len(row_cells)
                })

        # Step 2: loop through all exam rows
        for row_cells in grid:
            if not row_cells:
                continue
            # skip rows that are date rows
            if any(d for d in date_rows if d["row_cells"] == row_cells):
                continue

            # find the nearest date row above
            date_row = self.get_nearest_date_row(row_cells[0]["center_y"], date_rows)
            if not date_row:
                continue

            # Step 3: build date columns for this week
            date_columns = []
            for cell in date_row["row_cells"]:
                text = self.extract_text_from_bbox(page, cell["bbox"])
                date_match = re.search(r'(\d{2}/\d{2})', text)
                if date_match:
                    date_columns.append({
                        "date": date_match.group(1),
                        "x_center": cell["center_x"],
                        "x_min": cell["bbox"][0],
                        "x_max": cell["bbox"][2]
                    })
            date_columns.sort(key=lambda c: c["x_center"])
            if not date_columns:
                continue
            column_boundaries = [
                (date_columns[i]["x_center"] + date_columns[i+1]["x_center"])/2
                for i in range(len(date_columns)-1)
            ]

        print(f"   Dates: {[d['date'] for d in date_columns]}")
        
        if not date_columns:
            print("   ⚠️  No dates found")
            return []
        
        # Define column boundaries (midpoints between dates)
        column_boundaries = []
        for i in range(len(date_columns) - 1):
            mid = (date_columns[i]["x_center"] + date_columns[i+1]["x_center"]) / 2
            column_boundaries.append(mid)
        
        # Extract exam records
        exam_records = []
        
        for row_cells in grid:
            if not row_cells:
                continue
            # skip rows that are date rows
            if any(d for d in date_rows if d["row_cells"] == row_cells):
                continue

            # find the nearest date row above
            date_row = self.get_nearest_date_row(row_cells[0]["center_y"], date_rows)
            if not date_row:
                continue

            # build date columns for this week
            date_columns = []
            for cell in date_row["row_cells"]:
                text = self.extract_text_from_bbox(page, cell["bbox"])
                date_match = re.search(r'(\d{2}/\d{2})', text)
                if date_match:
                    date_columns.append({
                        "date": date_match.group(1),
                        "x_center": cell["center_x"],
                        "x_min": cell["bbox"][0],
                        "x_max": cell["bbox"][2]
                    })
            date_columns.sort(key=lambda c: c["x_center"])
            if not date_columns:
                continue

            column_boundaries = [
                (date_columns[i]["x_center"] + date_columns[i+1]["x_center"]) / 2
                for i in range(len(date_columns)-1)
            ]

            def find_column_index(x_center):
                for i, boundary in enumerate(column_boundaries):
                    if x_center < boundary:
                        return i
                return len(column_boundaries)

            # --- extract exam info for this row ---
            time_cell = row_cells[0]
            time_text = self.extract_text_from_bbox(page, time_cell["bbox"])
            times = re.findall(r'(\d{2})h(\d{2})', time_text)
            if not times:
                continue
            if len(times) >= 2:
                time_start = f"{times[0][0]}h{times[0][1]}"
                time_end = f"{times[1][0]}h{times[1][1]}"
            else:
                start_h, start_m = int(times[0][0]), int(times[0][1])
                end_h, end_m = start_h + 1, start_m + 30
                if end_m >= 60:
                    end_h += 1
                    end_m -= 60
                time_start = f"{start_h:02d}h{start_m:02d}"
                time_end = f"{end_h:02d}h{end_m:02d}"

            for cell in row_cells[1:]:
                subject_text = self.extract_text_from_bbox(page, cell["bbox"])
                if not subject_text or len(subject_text) < 3:
                    continue
                col_idx = find_column_index(cell["center_x"])
                if col_idx < len(date_columns):
                    date = date_columns[col_idx]["date"]
                    exam_records.append({
                        "Date": date,
                        "Time_Start": time_start,
                        "Time_End": time_end,
                        "Subject": subject_text,
                        "Class": class_level
                    })
        
        print(f"   ✓ Extracted {len(exam_records)} exam records")
        return exam_records

    def parse_calendar(self):
        """Main parsing pipeline"""
        print("="*60)
        print("📄 CALENDAR PARSER - YOLO + PyMuPDF")
        print("="*60)
        
        print("\n[1/3] Running YOLO detection...")
        num_pages = self.run_yolo_detection()
        print(f"✓ Detected cells on {num_pages} pages")
        
        print("\n[2/3] Extracting text from PDF...")
        doc = fitz.open(self.pdf_path)
        
        all_exam_records = []
        for page_num in range(1, num_pages + 1):
            records = self.parse_page(doc, page_num)
            all_exam_records.extend(records)
        
        doc.close()
        
        print("\n[3/3] Creating DataFrame...")
        df = pd.DataFrame(all_exam_records)
        
        if df.empty:
            print("\n⚠️  No exam records extracted!")
            return df
        
        # Sort by Date and Time
        df = df.sort_values(by=['Date', 'Time_Start', 'Class']).reset_index(drop=True)
        
        return df

def get_nearest_date_row(row_y,date_rows):
        # Pick the date row with the largest y_center smaller than the row's y
        candidates = [d for d in date_rows if d["y_center"] < row_y]
        if not candidates:
            return None
        return max(candidates, key=lambda d: d["y_center"])