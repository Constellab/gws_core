import { useEffect, useRef } from 'react';

import '/public/external/browser/styles.css';
import '/public/external/browser/light-theme.css';
import { dcInitComponents } from '/public/external/browser/dc-reflex.js';

await dcInitComponents();

export function InputSearchComponent({
    searchResult = null,
    selectedItem = null,
    itemSelected = null,
    searchTrigger = null,
    placeholder = null,
    required = null,
    minInputSearchLength = 2,
    initSearchOnFocus = false,
    pageSize = 20,
}) {
    const componentRef = useRef(null);

    // Set pageResult on the element when searchResult changes
    useEffect(() => {
        const element = componentRef.current;
        if (!element) return;
        element.pageResult = searchResult;
    }, [searchResult]);

    // Set selectedItem on the element when it changes
    useEffect(() => {
        const element = componentRef.current;
        if (!element) return;
        element.selectedItem = selectedItem;
    }, [selectedItem]);

    // Set up event listeners for output events
    useEffect(() => {
        const element = componentRef.current;
        if (!element) return;

        const handleItemSelected = (event) => {
            if (itemSelected) {
                itemSelected(event.detail);
            }
        };

        const handleSearchRequest = (event) => {
            console.log("Search request event detail:", event.detail);
            if (searchTrigger) {
                searchTrigger(event.detail);
            }
        };

        element.addEventListener('itemSelected', handleItemSelected);
        element.addEventListener('searchRequest', handleSearchRequest);

        return () => {
            element.removeEventListener('itemSelected', handleItemSelected);
            element.removeEventListener('searchRequest', handleSearchRequest);
        };
    }, [itemSelected, searchTrigger]);

    return (
        <dc-input-search
            ref={componentRef}
            placeholder={placeholder}
            required={required}
            minInputSearchLength={minInputSearchLength}
            initSearchOnFocus={initSearchOnFocus}
            pageSize={pageSize}
            style={{ display: 'flex', flexDirection: 'column', width: '100%' }}
        ></dc-input-search>
    );
}
