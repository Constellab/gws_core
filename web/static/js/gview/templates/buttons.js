new GViewTemplate({
    class: "gview:button",
    render: function (data) {
        function _btn(container, data){
            data.id = data.id || uuidv4()
            data.text = data.text || GView.defautTagData()
            data.href = data.href || ""
            data.target = data.target || ""
            data.variant = data.variant || "raised"

            if(! ["text", "raised", "outlined", "unelevated"].includes(data.variant) ){
                data.variant = "raised"
            }
            if(data.href != ""){
                container.innerHTML = `
                    <a id="`+ data.id +`" class="mdc-button mdc-button--`+data.variant+`" href="`+ data.href +`" target="`+ data.target +`"> 
                        <span class="mdc-button__ripple"></span>
                        `+ data.text.innerHTML +`
                    </a>
                `;
            } else{
                container.innerHTML = `
                    <button id="`+ data.id +`" class="mdc-button mdc-button--`+data.variant+`"> 
                        <span class="mdc-button__ripple"></span>
                        `+ data.text.innerHTML +`
                    </button>
                `;
            }
        }
        return _btn
    }
})