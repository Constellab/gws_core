new GViewTemplate({
    class: "gview:chip-set",
    render: function (data) {
        function _chips(container, data){
            data.id = data.id || uuidv4()
            var chips = []
            for(k in data.set){
                chips += `
                    <div class="mdc-chip" role="row">
                        <div class="mdc-chip__ripple"></div>
                        <span role="gridcell">
                            <span role="button" tabindex="0" class="mdc-chip__primary-action">
                                <a class="mdc-chip__text" href="`+data.set[k].href+`" style="text-decoration: none">`+data.set[k].text+`</a>
                            </span>
                        </span>
                    </div>
                `;
            }
            container.innerHTML = `
                <div id="chip-`+data.id+`" class="mdc-chip-set" role="grid">
                    ` + chips + `
                </div>
            `;
        }
        return _chips
    }
})