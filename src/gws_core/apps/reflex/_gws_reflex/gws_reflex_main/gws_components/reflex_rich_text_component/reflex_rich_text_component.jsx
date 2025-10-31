import { useEffect, useRef, useMemo } from 'react';

// Import scripts directly using ES6 import
// These will be loaded and executed when the module loads
import '/public/external/gws_plugin/main.js';

// Component that matches DcRichTextConfig interface
export function RichTextComponent({
  placeholder = null,
  value = null,
  disabled = null,
  minHeight = null,
  maxHeight = null,
  outputEvent = null  // Event handler callback
}) {
  const componentRef = useRef(null);

  // Combine all input data into a single JSON object
  const inputData = useMemo(() => ({
    placeholder,
    value,
    disabled,
    minHeight,
    maxHeight
  }), [placeholder, value, disabled, minHeight, maxHeight]);


  useEffect(() => {
    const element = componentRef.current;
    if (!element || !outputEvent) return;

    const handleEvent = (event) => {
      console.log('Received outputEvent from dc-text-editor:', JSON.stringify(event.detail));
      console.log(event.detail)
      outputEvent(event.detail);
      };

    element.addEventListener('outputEvent', handleEvent);

    return () => {
      element.removeEventListener('outputEvent', handleEvent);
    };
  }, [outputEvent]);

  return (
    <dc-text-editor
      ref={componentRef}
      inputData={JSON.stringify(inputData)}
      style={{ display: 'flex', flexDirection: 'column', width: '100%', 
        ...(disabled && { padding: '0' }) }}
    ></dc-text-editor>
  );
}
