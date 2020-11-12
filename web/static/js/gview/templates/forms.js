
new GViewTemplate({
    class: "gview:form",
    render: function (data) {

        function _form(container, data){
            var rows = ''
            data.style = data.style || ""
            data.title = data.title || ""
            data.valuetype = data.valuetype || "text"
            var fieldIds = [], fieldTypes = []
            for(var i in data.fields){   
                var uuid = uuidv4()
                if(data.fields[i].type == "hidden"){
                    rows += `
                        <input type="hidden" value="`+data.fields[i].value+`" name="`+data.fields[i].name+`">
                    `;
                } else{
                    data.fields[i].pattern = ''
                    if(data.fields[i].valuetype == "numeric" || data.fields[i].valuetype == "num"){
                        data.fields[i].pattern = 'pattern="-?[0-9]*(\.[0-9]+)?"'
                    }

                    if(data.fields[i].type == "text"){
                        rows += __gview_textField(uuid, data.fields[i]);
                        fieldIds.push('#mdc-'+uuid)
                        fieldTypes.push('text')
                    }else if(data.fields[i].type == "textarea"){
                        rows += __gview_textArea(uuid, data.fields[i]);
                        fieldIds.push('#mdc-'+uuid)
                        fieldTypes.push('textarea')
                    }else if(data.fields[i].type == "select"){
                        rows += __gview_Select(uuid, data.fields[i], data.selected);
                        fieldIds.push('#mdc-'+uuid)
                        fieldTypes.push('select')
                    }
                }
            }
            
            var submit = ""
            if(data.submit != null){
                var uuid = uuidv4()
                data.submit.variant = data.submit.variant || "raised"
                submit =  `
                    <br>
                    <button id="mdc-`+uuid+`" type="submit" class="mdc-button mdc-button--`+data.submit.variant+`" style="margin: 6px"> 
                        <span class="mdc-button__ripple"></span>
                        `+ data.submit.value +`
                    </button>
                `;
            }

            container.innerHTML = `
                <form action="`+data.submit.url+`" method="post">
                    ` + rows + submit + `
                </form>
            `;

            for(let i in fieldIds){
                var elem = document.querySelector(fieldIds[i])
                if(fieldTypes[i] == 'text'){
                    mdc.textField.MDCTextField.attachTo(elem);
                }else if (fieldTypes[i] == 'select'){
                    mdc.select.MDCSelect.attachTo(elem);
                }else if (fieldTypes[i] == 'textarea'){
                    mdc.textField.MDCTextField.attachTo(elem);
                }
            }

        }

        return _form
    }
})

function __gview_textField(uuid, field){
    field.newline = field.newline || "false"
    return `
    `+(field.newline == "true" ? "<br>" : "")+`
        <div id="mdc-`+uuid+`" class="mdc-text-field mdc-text-field--outlined" style="margin: 6px">
            <input class="mdc-text-field__input" `+field.pattern+` id="`+uuid+`" name="`+field.name+`" value="`+field.value+`">
            <div class="mdc-notched-outline">
                <div class="mdc-notched-outline__leading"></div>
                <div class="mdc-notched-outline__notch">
                    <label for="`+uuid+`" class="mdc-floating-label">`+field.label+`</label>
                </div>
                <div class="mdc-notched-outline__trailing"></div>
            </div>
        </div>`;
}

function __gview_textArea(uuid, field){
    field.newline = field.newline || "false"
    return `
    `+(field.newline == "true" ? "<br>" : "")+`
        <div id="mdc-`+uuid+`" class="mdc-text-field mdc-text-field--outlined mdc-text-field--textarea mdc-text-field--no-label" style="margin: 6px">
            <div class="mdc-text-field__resizer">
                <textarea class="mdc-text-field__input" rows="8" cols="40" aria-label="`+field.name+`">`+field.value+`</textarea>
            </div>
            <div class="mdc-notched-outline">
                <div class="mdc-notched-outline__leading"></div>
                <div class="mdc-notched-outline__notch">
                    <label for="`+uuid+`" class="mdc-floating-label">`+field.label+`</label>
                </div>
                <div class="mdc-notched-outline__trailing"></div>
            </div>
        </div>`;
}

function __gview_Select(uuid, field){
    field.selected = field.selected || ""
    var items = ""
    for(k in field.options){
        var selected = "false", css = ""
        if(field.selected == k){
            selected = "true";
            css = "mdc-list-item--selected"
        }

        items += `
            <li class="mdc-list-item `+css+`" aria-selected="`+selected+`" data-value="`+k+`" role="option">
                <span class="mdc-list-item__ripple"></span>
                <span class="mdc-list-item__text">
                    `+field.options[k]+`
                </span>
            </li>`;
    }
    field.newline = field.newline || "false"
    return `
        `+(field.newline == "true" ? "<br>" : "")+`
        <div id="mdc-`+uuid+`" class="mdc-select mdc-select--outlined" style="margin: 6px">
            <div class="mdc-select__anchor" aria-labelledby="outlined-select-label">
                <span class="mdc-notched-outline">
                    <span class="mdc-notched-outline__leading"></span>
                    <span class="mdc-notched-outline__notch">
                    <span id="outlined-select-label" class="mdc-floating-label">`+field.label+`</span>
                    </span>
                    <span class="mdc-notched-outline__trailing"></span>
                </span>
                <span class="mdc-select__selected-text-container">
                    <span id="demo-selected-text" class="mdc-select__selected-text"></span>
                </span>
                <span class="mdc-select__dropdown-icon">
                    <svg
                        class="mdc-select__dropdown-icon-graphic"
                        viewBox="7 10 10 5" focusable="false">
                    <polygon
                        class="mdc-select__dropdown-icon-inactive"
                        stroke="none"
                        fill-rule="evenodd"
                        points="7 10 12 15 17 10">
                    </polygon>
                    <polygon
                        class="mdc-select__dropdown-icon-active"
                        stroke="none"
                        fill-rule="evenodd"
                        points="7 15 12 10 17 15">
                    </polygon>
                    </svg>
                </span>
            </div>
            <div class="mdc-select__menu mdc-menu mdc-menu-surface mdc-menu-surface--fullwidth">
                <ul class="mdc-list" role="listbox" aria-label="`+field.label+`">
                    <li class="mdc-list-item `+(field.selected == "" ? "mdc-list-item--selected" : "false")+`" aria-selected="`+(field.selected == "" ? "true" : "false")+`" data-value="" role="option">
                        <span class="mdc-list-item__ripple"></span>
                    </li>
                    `+items+`
                </ul>
            </div>
        </div>

    `;
}