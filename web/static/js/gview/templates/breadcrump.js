new GViewTemplate({
    class: "gview:breadcrump",
    render: function (data) {
        function _chips(container, data){
            data.id = data.id || uuidv4()
            data.sep = data.sep || ">"

            var chips = []
            for(k in data.list){
                chips.push(`
                    <a class="mdc-chip__text" href="/page/biota" style="text-decoration: none">`+data.list[k].text+`</a>
                `);
            }
            container.innerHTML = `
                <div id="chip-`+data.id+`" class="mdc-chip-set" role="grid" style="margin-bottom: 12px">

                    <div class="mdc-chip" role="row">
                        <div class="mdc-chip__ripple"></div>
                            <span role="gridcell">
                                <span role="button" tabindex="0" class="mdc-chip__primary-action">
                                    ` + chips.join(data.sep) + `
                                </span>
                            </span>
                        </div>
                    </div>

                </div>
            `;
        }
        return _chips
    }
})