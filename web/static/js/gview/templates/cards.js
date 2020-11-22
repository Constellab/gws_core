new GViewTemplate({
    class: "gview:card",
    render: function (data) {
        function _card(container, data){
            data.class = (data.class != null) || "mdc-card-md"
            data.style = data.style || ""
            data.title = data.title || GView.defautTagData()
            data.subtitle = data.subtitle || GView.defautTagData()
            data.body = data.body || GView.defautTagData()
            data.titleImg = data.titleImg || GView.defautTagData()
            data.titleHeight = data.titleHeight || GView.defautTagData()

            container.innerHTML = `
                <div class="mdc-card `+data.class+`" style="`+data.style+`" >
                    <div class="mdc-card__primary-action" tabindex="0">
                        <div class="mdc-card__media" style="padding: 0px 16px;">
                            <h2 class="mdc-card-title mdc-typography mdc-typography--headline6">`+data.title.innerHTML+`</h2>
                            <h3 class="mdc-card-subtitle mdc-typography mdc-typography--subtitle2">`+data.subtitle.innerHTML+`</h3>
                        </div>
                        <div class="mdc-card-body mdc-typography mdc-typography--body2" style="padding: 0px 16px;">
                            `+data.body.innerHTML+`
                        </div>
                    </div>
                    `+ __createAction(data) +`
                </div>
            `;
        }
        return _card
    }
})


function __createAction(data){
    var actionButtonHTML = ""
    var actionNames = ["action_button_1", "action_button_2", "action_button_3"]

    for(k of actionNames){
        if(data[k] == null)
            continue

        var attr = ""
        for(s in data[k]){
            attr = s + "=" + data[k][s] + " "
        } 

        if( data[k].href != null ){
            data[k].target = data[k].target || ""
            actionButtonHTML += `
                <a `+attr+` class="mdc-button mdc-card__action mdc-card__action--button" href="`+data[k].href+`" target="`+data[k].target+`">  <span class="mdc-button__ripple"></span>`+data[k].innerHTML+`</a>
            `;
        } else{
            actionButtonHTML += `
                <button `+attr+` class="mdc-button mdc-card__action mdc-card__action--button">  <span class="mdc-button__ripple"></span>`+data[k].innerHTML+`</button>
            `;
        }
    }
    
    if(actionButtonHTML != ""){
        actionButtonHTML = `
            <div class="mdc-card__action-buttons">
                `+actionButtonHTML+`
            </div>
        `;
    }

    var actionIconHTML = ""
    var actionNames = ["action_icon_1", "action_icon_2", "action_icon_3"]
    for(k of actionNames){
        if(data[k] == null)
            continue
        
        var attr = ""
        for(s in data[k]){
            attr = s + "=" + data[k][s] + " "
        } 

        if( data[k].href != null ){
            data[k].target = data[k].target || ""
            actionIconHTML += `
                <a `+attr+` class="mdc-icon-button material-icons mdc-card__action mdc-card__action--icon--unbounded" href="`+data[k].href+`" target="`+data[k].target+`" title="`+data[k].innerHTML+`" data-mdc-ripple-is-unbounded="true">`+data[k].innerHTML+`</a>
            `;
        }else{
            actionIconHTML += `
                <button `+attr+` class="mdc-icon-button material-icons mdc-card__action mdc-card__action--icon--unbounded" title="`+data[k].innerHTML+`" data-mdc-ripple-is-unbounded="true">`+data[k].innerHTML+`</button>
            `;
        }
    }
    if( actionIconHTML != ""){
         actionIconHTML = `
            <div class="mdc-card__action-icons">
                `+ actionIconHTML+`
            </div>
        `;
    }

    var actionHTML = ""
    if(actionButtonHTML != "" || actionIconHTML != ""){
        actionHTML = `
            <div class="mdc-card__actions">
                ` + actionButtonHTML + actionIconHTML + `
            </div>
        `;
    }
    return actionHTML
}