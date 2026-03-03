import plotly.graph_objects as go
import reflex as rx
from gws_reflex_base.component.reflex_dialog_components import dialog_header


class PlotlyFullscreenState(rx.State):
    """State management for Plotly fullscreen dialog.

    Manages the display of Plotly figures in a fullscreen modal dialog,
    allowing users to view charts in a larger format.

    Attributes:
        is_dialog_open: Whether the fullscreen dialog is currently open
        message: Dict containing 'figure' and 'plot_name' keys
    """

    is_dialog_open: bool = False
    # use a dict to avoid errors with go.Figure serialization in Reflex state
    message: dict | None = None

    def open_dialog(self, message: dict):
        """Open the fullscreen dialog with the given figure.

        Args:
            message: Dict with 'figure' (Plotly figure) and 'plot_name' (optional title)
        """
        self.message = message
        self.is_dialog_open = True

    def close_dialog(self):
        """Close the fullscreen dialog and clear the current figure."""
        self.is_dialog_open = False
        self.message = None

    def set_is_dialog_open(self, is_open: bool):
        """Set the dialog open state.

        Args:
            is_open: Whether the dialog should be open
        """
        self.is_dialog_open = is_open


def plotly_fullscreen_dialog() -> rx.Component:
    """Create a fullscreen dialog component to display Plotly figures.

    This dialog displays a Plotly figure in a large modal view, allowing
    users to see charts with more detail and interact with them more easily.

    This component should be rendered exactly once in the page layout.

    Returns:
        rx.Component: A dialog component with fullscreen Plotly display
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                dialog_header(
                    title=rx.cond(
                        PlotlyFullscreenState.message,
                        PlotlyFullscreenState.message["plot_name"],
                        "Chart",
                    ),
                    close=PlotlyFullscreenState.close_dialog,
                ),
                # Plotly figure
                rx.box(
                    rx.plotly(
                        data=rx.cond(
                            PlotlyFullscreenState.message["figure"],
                            PlotlyFullscreenState.message["figure"],
                            go.Figure(),
                        ),
                        width="100%",
                        height="100%",
                    ),
                    width="100%",
                    flex="1",
                    min_height="0",
                    padding="12px 0",
                ),
                spacing="0",
                width="100%",
                height="100%",
            ),
            max_width="95vw",
            height="95vh",
            width="95vw",
        ),
        open=PlotlyFullscreenState.is_dialog_open,
        on_open_change=PlotlyFullscreenState.set_is_dialog_open,
    )


def plotly_with_fullscreen(figure: rx.Var, plot_name: rx.Var | str = "Chart") -> rx.Component:
    """Render a Plotly chart with a hover-visible fullscreen expand button.

    This component wraps a Plotly figure with an overlay button that appears
    on hover, allowing users to open the chart in a fullscreen dialog.

    The plotly_fullscreen_dialog() must be rendered once in the page layout
    for the fullscreen functionality to work.

    Args:
        figure: The Plotly figure Var to display
        plot_name: Name/title for the plot shown in the fullscreen dialog

    Returns:
        rx.Component: Plotly chart with fullscreen button overlay
    """
    return rx.box(
        rx.plotly(
            data=rx.cond(figure, figure, go.Figure()),
            width="100%",
        ),
        rx.tooltip(
            rx.button(
                rx.icon("expand", size=14),
                position="absolute",
                top="2px",
                left="2px",
                size="1",
                variant="soft",
                on_click=PlotlyFullscreenState.open_dialog(
                    {
                        "figure": figure,
                        "plot_name": plot_name,
                    }
                ),
                cursor="pointer",
                background_color="var(--gray-1)",
                opacity="0",
                transition="opacity 0.2s ease",
                class_name="plotly-fullscreen-btn",
            ),
            content="Open in fullscreen",
            side="bottom",
        ),
        position="relative",
        width="100%",
        style={
            "&:hover .plotly-fullscreen-btn": {
                "opacity": "1",
            }
        },
    )
