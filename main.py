# Entry point for the application
from UI.saba_ui_manager import SabaUIManager

def main():
    """
    Main entry point that integrates UI with speech functionality.
    The UI will remain open and automatically listen for speech until manually closed.
    """
    # Create and initialize the UI manager
    ui_manager = SabaUIManager()
    ui_manager.initialize()
    
    # Start the integrated UI and speech system
    # This will keep running until the UI window is closed
    return ui_manager.start_with_speech()

def play():
    """
    Public function that main can invoke to start the UI with speech functionality.
    This function will not return until the UI is closed by the user.
    """
    return main()

if __name__ == "__main__":
    main()
