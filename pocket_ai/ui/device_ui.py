from pocket_ai.core.logger import logger

class DeviceUI:
    def show_home(self):
        logger.info("UI: Showing Home Screen")
    
    def show_listening(self):
        logger.info("UI: Listening...")
        
    def show_response(self, text: str):
        logger.info(f"UI: Showing Response: {text}")

device_ui = DeviceUI()
