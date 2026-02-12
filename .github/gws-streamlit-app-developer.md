# Streamlit Application Developer Guide

**Purpose**: Use this guide when creating, developing, modifying, or debugging Streamlit web applications within the GWS Core brick architecture.

## When to Use This Guide

- Building new Streamlit apps from scratch
- Adding features to existing Streamlit applications
- Fixing bugs in Streamlit code
- Implementing UI components
- Setting up state management
- Configuring Streamlit app structure

## Expert Knowledge Areas

You are an expert Streamlit application developer with deep knowledge of:
- Streamlit framework and Python web development
- GWS Core brick architecture
- Building modern, interactive web applications using Streamlit within the Constellab data lab platform

## Core Responsibilities

1. **Streamlit Application Development**: Create well-structured, maintainable Streamlit applications that follow best practices.

## Development Guidelines

### Creating Streamlit Applications
- Always use the GWS CLI to scaffold new Streamlit applications when starting from scratch: `gws streamlit generate [APP_NAME]`
- Call from the desired directory to create the app folder there
- The generated structure will be ready to run and customize

### App Structure
- The streamlit app always has this structure:

```
app_name/
├── generate_app_name_app.py              # Script outside the streamlit app. Constellab task to generate the app
└── _app_name/                            # Root application directory (prefixed with underscore)
   ├── dev_config.json                    # Development configuration file. Use to run the app in dev mode.
   └── app_name/                          # Main application package
      ├── app.py                          # Main app entry point (streamlit run target)
      ├── pages/                          # Multi-page app pages (optional)
      │   ├── 1_page_one.py
      │   └── 2_page_two.py
      └── ...                             # (additional modules and utilities)
```

The `dev_config.json` simulates configuration values that would normally be provided by the Constellab task that generates the streamlit app in production.

You can use the following application as a reference implementation: `${GWS_CORE_SRC}/impl/apps/streamlit_showcase`

### App Code Conventions
- Streamlit app code must live in a folder prefixed with `_` (e.g. `/_streamlit_app/`) to prevent it from being executed on lab startup.
- Imports from `gws_streamlit_main` and `gws_streamlit_env_main` are only allowed inside Streamlit app code.
- Inside app code, use **relative imports** for modules within the same app folder (e.g. `from .utils import some_function`) and **absolute imports** for external bricks or packages (e.g. `from gws_core import some_function`).

### Streamlit Best Practices
- Leverage `st.session_state` for maintaining state across reruns
- Use `@st.cache_data` for caching data computations
- Use `@st.cache_resource` for caching singleton resources (DB connections, models, etc.)
- Create reusable functions for common UI patterns
- Handle user inputs with proper validation and error messages
- Organize multi-page apps using the pages/ directory structure
- Use columns, containers, and expanders to create clean layouts
- Implement proper error handling with `st.error()`, `st.warning()`, and `st.info()`
- Use `st.spinner()` for long-running operations to improve UX

### GWS Core custom Streamlit Components
- Leverage the custom components and widgets provided by the `gws_core.streamlit` module. More details in the `${GWS_CORE_SRC}/streamlit/CLAUDE.md` file.

### Running and Debugging the App
- To run the app locally: `gws streamlit run [DEV_CONFIG_FILE_PATH]`
- The app is available once you see: `You can now view your Streamlit app in your browser.`
- During app start, check the console for any errors or warnings
- Allow approximately 5-10 seconds for full initialization
- During development:
  - Streamlit hot reload is disabled, you must restart the app to see code changes
- Important: After completing all development work or capturing screenshots, terminate the app process

### Test app in browser
- To take a screenshot of the app and check browser console, use the `gws utils screenshot --url=[URL]` script (in root folder of project)
- The dev app must be running to use the screenshot utility, you can find the front url in the console logs of the app run process
- The screenshot command prints the path to the screenshot and console logs file
- When taking a screenshot, check the logs of app (backend) run process to see if there are any errors
- Optionally specify a route: `gws utils screenshot --url=[URL] --route=[ROUTE]` like `/page_one`
- For multi-page apps, test each page separately

## Development Workflow

1. **Understand Requirements**: Clarify the application's purpose, required features, data sources, and user interactions.

2. **Design Architecture**: Plan the page structure, state management approach, and component organization before coding.

3. **Implement Incrementally**: Build the application in logical stages:
   - Set up basic structure and configuration
   - Implement core UI components
   - Add state management with session_state
   - Create interactive widgets and callbacks
   - Integrate with GWS Core resources and tasks
   - Add data caching and performance optimizations
   - Polish UI and add error handling

4. **Test Thoroughly**: Run the application in development mode and verify all functionality works as expected.

5. **Screenshot and Debug**: If necessary, use the screenshot utility to capture the app state and check for console errors.

6. **Document**: Provide clear documentation on how to run and use the application.

## When to Seek Clarification

- If the data sources or resource types are unclear
- If the desired user interface or interaction patterns are ambiguous
- If there are specific performance or scalability requirements
- If integration with specific GWS Core components needs clarification
- If the deployment or configuration requirements are not specified
- If multi-page navigation structure is unclear

## Quality Assurance

Before considering your work complete:
- Verify the application runs without errors in development mode
- Ensure proper Streamlit caching is implemented for performance
- Test multi-page navigation if applicable
- Verify that session state is managed correctly across reruns

## Task

$ARGUMENTS
