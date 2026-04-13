import { useEffect, useMemo, useRef } from 'react';

import '/public/external/gws_plugin/styles.css';
import '/public/external/gws_plugin/light-theme.css';
import { dcInitComponents } from '/public/external/gws_plugin/dc-reflex.js';
await dcInitComponents();

export function SelectResource2Component({
    inputData = null,
    authenticationInfo = null,
    outputEvent = null,
}) {
    const componentRef = useRef(null);
    const inputDataCountRef = useRef(0);

    const inputDataMemo = useMemo(() => inputData, [inputData]);

    // Set inputData on the element when it changes
    useEffect(() => {
        const element = componentRef.current;
        if (!element) return;

        inputDataCountRef.current += 1;
        const dataWithCount = { ...(inputDataMemo || {}), __count__: inputDataCountRef.current };
        element.inputData = JSON.stringify(dataWithCount);
    }, [inputDataMemo]);

    // Set up event listener for output events
    useEffect(() => {
        const element = componentRef.current;
        if (!element) return;

        if (!outputEvent) return;

        const handleEvent = (event) => {
            outputEvent(event.detail);
        };

        element.addEventListener('outputEvent', handleEvent);

        return () => {
            element.removeEventListener('outputEvent', handleEvent);
        };
    }, [outputEvent]);

    return (
        <dc-select-resource
            ref={componentRef}
            authenticationInfo={JSON.stringify(authenticationInfo)}
            style={{ display: 'flex', flexDirection: 'column', width: '100%' }}
        ></dc-select-resource>
    );
}
