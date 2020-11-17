new GViewTemplate({
    class: "gview:breadcrump",
    render: function (data) {
        function _chips(container, data){
            data.id = data.id || uuidv4()
            data.sep = data.sep || ">"

            var chips = []
            for(k in data.list){
                chips.push(`
                    <a href="`+data.list[k].href+`">` + data.list[k].text + `</a>
                `);
            }
            container.innerHTML = `<div class="mdc-breadcrump">` +chips.join(data.sep) + `</div>`
        }
        return _chips
    }
})