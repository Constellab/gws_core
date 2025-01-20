from main_streamlit_app_runner import StreamlitMainAppRunner

streammlit_app = StreamlitMainAppRunner()

streammlit_app.init()

config = streammlit_app.config

# load resources
source_paths = config['source_ids']

streammlit_app.set_variable('source_paths', source_paths)
streammlit_app.set_variable('params', config['params'])

streammlit_app.start_app()
