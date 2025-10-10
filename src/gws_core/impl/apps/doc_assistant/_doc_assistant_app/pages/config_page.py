import json
import os

import streamlit as st

from gws_core.streamlit import StreamlitContainers


def load_prompts(prompts_json_path: str) -> dict:
    """Load prompts from JSON file"""
    if not os.path.exists(prompts_json_path):
        st.error(f"Prompts file not found: {prompts_json_path}")
        return {}

    try:
        with open(prompts_json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading prompts file: {str(e)}")
        return {}


def save_prompts(prompts_json_path: str, prompts: dict) -> bool:
    """Save prompts to JSON file"""
    try:
        with open(prompts_json_path, 'w') as f:
            json.dump(prompts, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving prompts file: {str(e)}")
        return False


def render_config_page(prompts_json_path: str):
    """Render the config page for managing prompts"""

    with StreamlitContainers.container_centered('config'):

        st.title("Prompt Configuration")

        # Load prompts
        prompts = load_prompts(prompts_json_path)

        # Create new prompt section
        st.subheader("Create New Prompt")

        col1, col2 = st.columns(2)

        with col1:
            new_prompt_name = st.text_input(
                "Prompt Name",
                key="new_prompt_name",
                placeholder="e.g., API Documentation"
            )

        with col2:
            # Empty column for spacing
            st.write("")

        new_prompt_text = st.text_area(
            "Prompt Text",
            key="new_prompt_text",
            placeholder="Enter the prompt text...",
            height=100
        )

        if st.button("Create Prompt", type="primary"):
            if not new_prompt_name:
                st.error("Please enter a prompt name.")
            elif not new_prompt_text:
                st.error("Please enter prompt text.")
            elif new_prompt_name in prompts:
                st.error(f"Prompt '{new_prompt_name}' already exists. Please use a different name.")
            else:
                prompts[new_prompt_name] = new_prompt_text
                if save_prompts(prompts_json_path, prompts):
                    st.success(f"Prompt '{new_prompt_name}' created successfully!")
                    st.rerun()

        st.divider()

        # Edit existing prompts section
        st.subheader("Manage Existing Prompts")

        if not prompts:
            st.warning("No prompts available. Create your first prompt above.")
            return

        # Display prompts in expandable sections
        for prompt_name in list(prompts.keys()):
            with st.expander(f"📝 {prompt_name}", expanded=False):

                # Store the original prompt name for updates
                prompt_key = f"prompt_{prompt_name.replace(' ', '_').lower()}"

                # Edit prompt name
                updated_name = st.text_input(
                    "Prompt Name",
                    value=prompt_name,
                    key=f"{prompt_key}_name"
                )

                # Edit prompt text
                updated_text = st.text_area(
                    "Prompt Text",
                    value=prompts[prompt_name],
                    key=f"{prompt_key}_text",
                    height=150
                )

                col1, col2, col3 = st.columns([1, 1, 4])

                with col1:
                    # Update button
                    if st.button("Update", key=f"{prompt_key}_update"):
                        if not updated_name:
                            st.error("Prompt name cannot be empty.")
                        elif not updated_text:
                            st.error("Prompt text cannot be empty.")
                        elif updated_name != prompt_name and updated_name in prompts:
                            st.error(f"Prompt '{updated_name}' already exists.")
                        else:
                            # Remove old prompt if name changed
                            if updated_name != prompt_name:
                                del prompts[prompt_name]

                            # Add/update prompt with new values
                            prompts[updated_name] = updated_text

                            if save_prompts(prompts_json_path, prompts):
                                st.success(f"Prompt '{updated_name}' updated successfully!")
                                st.rerun()

                with col2:
                    # Delete button
                    if st.button("Delete", key=f"{prompt_key}_delete", type="secondary"):
                        # Confirm deletion using a dialog or session state flag
                        if f"{prompt_key}_confirm_delete" not in st.session_state:
                            st.session_state[f"{prompt_key}_confirm_delete"] = False

                        if not st.session_state[f"{prompt_key}_confirm_delete"]:
                            st.session_state[f"{prompt_key}_confirm_delete"] = True
                            st.rerun()

                # Handle deletion confirmation
                if f"{prompt_key}_confirm_delete" in st.session_state and st.session_state[f"{prompt_key}_confirm_delete"]:
                    st.warning(f"⚠️ Are you sure you want to delete '{prompt_name}'?")
                    col_confirm, col_cancel = st.columns(2)

                    with col_confirm:
                        if st.button("Yes, Delete", key=f"{prompt_key}_confirm_yes"):
                            del prompts[prompt_name]
                            if save_prompts(prompts_json_path, prompts):
                                st.success(f"Prompt '{prompt_name}' deleted successfully!")
                                del st.session_state[f"{prompt_key}_confirm_delete"]
                                st.rerun()

                    with col_cancel:
                        if st.button("Cancel", key=f"{prompt_key}_confirm_no"):
                            del st.session_state[f"{prompt_key}_confirm_delete"]
                            st.rerun()

        st.divider()

        # Display total count
        st.info(f"Total prompts: {len(prompts)}")
