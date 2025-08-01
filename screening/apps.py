from django.apps import AppConfig
import threading
import os


class ScreeningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'screening'

    def ready(self):
        # Download NLTK data in a separate thread to avoid blocking app startup
        thread = threading.Thread(target=self.download_nltk_data)
        thread.daemon = True
        thread.start()
    
    def download_nltk_data(self):
        try:
            import nltk
            from nltk.data import find
            
            # Check if the required NLTK data is already downloaded
            required_data = ['punkt', 'wordnet', 'omw-1.4']
            missing_data = []
            
            for item in required_data:
                try:
                    find(f'tokenizers/{item}' if item == 'punkt' else f'corpora/{item}')
                except LookupError:
                    missing_data.append(item)
            
            # Only download missing data
            if missing_data:
                for item in missing_data:
                    nltk.download(item)
                print(f"NLTK data downloaded: {', '.join(missing_data)}")
            else:
                # No need to print anything if all data is already available
                pass
        except Exception as e:
            print(f"Error checking/downloading NLTK data: {str(e)}")
