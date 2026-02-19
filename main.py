# import os
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
# os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# import logging
# logging.getLogger("llama_index").setLevel(logging.ERROR)

# from ui.onboarding import run_onboarding_if_needed

# def launch_main_app(memory):
#     from ui.app import ZigsyApp
#     app = ZigsyApp(memory=memory)
#     app.mainloop()

# if __name__ == "__main__":
#     run_onboarding_if_needed(launch_main_app)

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import logging
logging.getLogger("llama_index").setLevel(logging.ERROR)

from core.llm import chat
from core.rag import load_or_build_index, get_context
from core.memory import load_memory, get_memory_context, add_confusion, add_note
from tools.screen_context import get_active_window_info

if __name__ == "__main__":
    from ui.app import ZigsyApp
    app = ZigsyApp()
    app.mainloop()