import { useEffect, useRef, useMemo, useState } from 'react';

// Import scripts directly using ES6 import
// These will be loaded and executed when the module loads
// import '/public/external/gws_plugin/main.js';
import '/public/external/gws_plugin/styles.css';
import '/public/external/gws_plugin/light-theme.css';
import { dcInitComponents } from '/public/external/browser/dc-reflex.js';
// Initialize the web components
await dcInitComponents();


/**
 * Custom hook to load custom tools from /public/custom_block.jsx
 * @param {boolean} enabled - Whether to load custom tools
 * @param {object|null} authenticationInfo - Authentication info to pass to the custom tools factory
 * @returns {{ customTools: object|null, error: string|null }}
 */
function useCustomToolsLoader(enabled, authenticationInfo) {
  const [customTools, setCustomTools] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!enabled) {
      setCustomTools(null);
      setError(null);
      return;
    }

    setError(null);

    import('/public/custom_block.jsx')
      .then((module) => {
        if (!module.getCustomTools) {
          throw new Error(
            "The file '/public/custom_block.jsx' was loaded but does not export a 'getCustomTools' function. " +
            "Please ensure the file contains: export function getCustomTools(authenticationInfo) { ... }"
          );
        }
        if (typeof module.getCustomTools !== 'function') {
          throw new Error(
            "The 'getCustomTools' export in '/public/custom_block.jsx' must be a function. " +
            `Received: ${typeof module.getCustomTools}`
          );
        }
        const tools = module.getCustomTools(authenticationInfo);
        if (typeof tools !== 'object' || tools === null) {
          throw new Error(
            "The 'getCustomTools' function in '/public/custom_block.jsx' must return an object. " +
            `Received: ${typeof tools}`
          );
        }
        setCustomTools(tools);
      })
      .catch((err) => {
        let errorMessage;
        if (err.message?.includes('Failed to fetch') || err.message?.includes('404')) {
          errorMessage =
            "Failed to load custom tools: The file '/public/custom_block.jsx' was not found. " +
            "Please ensure the file exists in your app's assets folder and will be served at '/public/custom_block.jsx'.";
        } else if (err.message?.includes('SyntaxError') || err.name === 'SyntaxError') {
          errorMessage =
            "Failed to load custom tools: Syntax error in '/public/custom_block.jsx'. " +
            `Please check the file for JavaScript syntax errors. Details: ${err.message}`;
        } else {
          errorMessage =
            `Failed to load custom tools from '/public/custom_block.jsx': ${err.message}`;
        }
        console.error('[RichTextComponent] Custom tools loading error:', errorMessage, err);
        setError(errorMessage);
      });
  }, [enabled, authenticationInfo]);

  return { customTools, error };
}

// Component that matches DcRichTextConfig interface
export function RichTextComponent({
  placeholder = null,
  value = null,
  disabled = null,
  changeEventDebounceTime = null,
  outputEvent = null,  // Event handler callback
  customStyle = {},
  useCustomTools = false,  // Whether to load custom tools from /public/custom_block.jsx
  authenticationInfo = null,
}) {
  const componentRef = useRef(null);
  const { customTools, error: customToolsError } = useCustomToolsLoader(useCustomTools, authenticationInfo);

  // Combine all input data into a single JSON object
  const inputData = useMemo(() => ({
    placeholder,
    value,
    disabled,
    changeEventDebounceTime,
  }), [placeholder, value, disabled, changeEventDebounceTime]);

  // Set up the component and event listeners
  useEffect(() => {
    const element = componentRef.current;
    if (!element) return;

    // Set customTools directly on the element (can't be passed as JSON since it contains class references)
    // Only set if we have loaded custom tools or if useCustomTools is false
    if (customTools) {
      element.customTools = customTools;
    }

    if (!outputEvent) return;

    const handleEvent = (event) => {
      outputEvent(event.detail);
    };

    element.addEventListener('outputEvent', handleEvent);

    return () => {
      element.removeEventListener('outputEvent', handleEvent);
    };
  }, [outputEvent, customTools]);

  // Show error message if custom tools failed to load
  if (customToolsError) {
    return (
      <div style={{
        padding: '16px',
        backgroundColor: '#fee2e2',
        border: '1px solid #ef4444',
        borderRadius: '8px',
        color: '#991b1b',
        fontFamily: 'system-ui, sans-serif'
      }}>
        <strong style={{ display: 'block', marginBottom: '8px' }}>
          ⚠️ Rich Text Component Error
        </strong>
        <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{customToolsError}</p>
      </div>
    );
  }

  return (
    <dc-text-editor
      ref={componentRef}
      inputData={JSON.stringify(inputData)}
      useCustomTools={useCustomTools ? 'true' : 'false'}
      authenticationInfo={JSON.stringify(authenticationInfo)}
      style={{ display: 'flex', flexDirection: 'column', width: '100%',
       ...(customStyle || {}) }}
    ></dc-text-editor>
  );
}
