# entrypoints/main.py - Production Entry Point for Comic/Manga Automation
import sys
import os

# Add root to sys.path for production execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.main_pipeline import ComicAutomationPipeline

def main():
    """
    Mature entry point. Delegates to main_pipeline.py.
    Maintains compatibility with existing trigger scripts.
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_file_or_url>")
        return

    input_path = sys.argv[1]
    pipeline = ComicAutomationPipeline()
    pipeline.run_pipeline(input_path)

if __name__ == "__main__":
    main()
