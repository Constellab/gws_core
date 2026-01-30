import { useEffect, useRef, useMemo, useState } from 'react';

// Import scripts directly using ES6 import
import '/public/external/gws_plugin/styles.css';
import '/public/external/gws_plugin/light-theme.css';
import { dcInitComponents } from '/public/external/gws_plugin/dc-reflex.js';
// Initialize the web components
await dcInitComponents();


/**
 * Normalize asset path for dev/prod mode compatibility.
 * In dev mode (Vite dev server), static assets in /public need the /public prefix for dynamic imports.
 * In prod mode (built/bundled), assets are served from root without the /public prefix.
 * @param {string} path - The asset path (e.g., '/external/app/file.js')
 * @returns {string} The normalized path with /public prefix in dev mode
 */
function normalizeAssetPath(path) {
  if (!path) return path;
  // In dev mode, add /public prefix if not already present
  if (import.meta.env.DEV && !path.startsWith('/public')) {
    return '/public' + path;
  }
  return path;
}


/**
 * Custom hook to load custom tools from a JSX file specified in customToolsConfig.
 * @param {object|null} customToolsConfig - Configuration with jsxFilePath and optional config dict
 * @param {object|null} authenticationInfo - Authentication info to pass to the custom tools factory
 * @returns {{ customTools: object|null, error: string|null }}
 */
function useCustomToolsLoader(customToolsConfig, authenticationInfo, customToolsEvent) {
  const [customTools, setCustomTools] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!customToolsConfig || !customToolsConfig.jsxFilePath) {
      setCustomTools(null);
      setError(null);
      return;
    }

    // Normalize the path for dev/prod mode compatibility
    const jsxFilePath = normalizeAssetPath(customToolsConfig.jsxFilePath);

    setError(null);
    // Pre-compute the dc-reflex.js path for custom tools to use
    const DC_REFLEX_PATH = normalizeAssetPath('/external/gws_plugin/dc-reflex.js');


    import(jsxFilePath)
      .then((module) => {
        if (!module.getCustomTools) {
          throw new Error(
            `The file '${jsxFilePath}' was loaded but does not export a 'getCustomTools' function. ` +
            "Please ensure the file contains: export function getCustomTools(config, authenticationInfo) { ... }"
          );
        }
        if (typeof module.getCustomTools !== 'function') {
          throw new Error(
            `The 'getCustomTools' export in '${jsxFilePath}' must be a function. ` +
            `Received: ${typeof module.getCustomTools}`
          );
        }
        // Add dcReflexPath to config so custom tools can import from dc-reflex.js
        const configWithPaths = {
          ...customToolsConfig,
          dcReflexPath: DC_REFLEX_PATH,
        };
        const tools = module.getCustomTools(configWithPaths, authenticationInfo, customToolsEvent);
        if (typeof tools !== 'object' || tools === null) {
          throw new Error(
            `The 'getCustomTools' function in '${jsxFilePath}' must return an object. ` +
            `Received: ${typeof tools}`
          );
        }
        setCustomTools(tools);
      })
      .catch((err) => {
        let errorMessage;
        if (err.message?.includes('Failed to fetch') || err.message?.includes('404')) {
          errorMessage =
            `Failed to load custom tools: The file '${jsxFilePath}' was not found. ` +
            "Please ensure the file exists in your app's assets folder.";
        } else if (err.message?.includes('SyntaxError') || err.name === 'SyntaxError') {
          errorMessage =
            `Failed to load custom tools: Syntax error in '${jsxFilePath}'. ` +
            `Please check the file for JavaScript syntax errors. Details: ${err.message}`;
        } else {
          errorMessage =
            `Failed to load custom tools from '${jsxFilePath}': ${err.message}`;
        }
        console.error('[RichTextComponent] Custom tools loading error:', errorMessage, err);
        setError(errorMessage);
      });
  }, [customToolsConfig, authenticationInfo, customToolsEvent]);

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
  customToolsConfig = null,
  authenticationInfo = null,
  customToolsEvent = null,
}) {
  const componentRef = useRef(null);
  const inputDataCountRef = useRef(0);
  const { customTools, error: customToolsError } = useCustomToolsLoader(customToolsConfig, authenticationInfo, customToolsEvent);


  // Combine all input data into a single JSON object
  const inputData = useMemo(() => ({
    placeholder,
    value,
    disabled,
    changeEventDebounceTime,
  }), [placeholder, value, disabled, changeEventDebounceTime]);

  // Set inputData as a property on the element so the web component picks up changes
  useEffect(() => {
    const element = componentRef.current;
    if (!element) return;

    // Increment __count__ to force a change in inputData even when the value is the same as the
    // previously sent one. This is needed for rollback scenarios where the outer value reverts to a
    // previous state but the dc component's inner value has diverged and must be overwritten.
    inputDataCountRef.current += 1;
    const dataWithCount = { ...inputData, __count__: inputDataCountRef.current };
    element.inputData = JSON.stringify(dataWithCount);
  }, [inputData]);

  // Set up the component and event listeners
  useEffect(() => {
    const element = componentRef.current;
    if (!element) return;

    // Set customTools directly on the element (can't be passed as JSON since it contains class references)
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

  const hasCustomTools = customToolsConfig && typeof customToolsConfig === 'object' && customToolsConfig.jsxFilePath;

  return (
    <dc-text-editor
      ref={componentRef}
      useCustomTools={hasCustomTools ? 'true' : 'false'}
      authenticationInfo={JSON.stringify(authenticationInfo)}
      style={{
        display: 'flex', flexDirection: 'column', width: '100%',
        ...(customStyle || {})
      }}
    ></dc-text-editor>
  );
}
