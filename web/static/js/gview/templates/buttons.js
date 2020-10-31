new GViewTemplate({
    class: "gview:button",
    render: function (data) {
        function _btn(container, data){
            data.id = data.id || uuidv4()
            data.text = data.text || ""
            data.href = data.href || ""
            data.target = data.target || ""
            if(data.href != ""){
                container.innerHTML = `
                    <a class="mdl-button mdl-js-button mdl-button--raised mdl-button--colored mdl-js-ripple-effect" id="`+ data.id +`" href="`+ data.href +`" target="`+ data.target +`">
                        `+ data.text +`
                    </a>
                `;
            } else{
                container.innerHTML = `
                    <button class="mdl-button mdl-js-button mdl-button--raised mdl-button--colored mdl-js-ripple-effect" id="`+ data.id +`">
                        `+ data.text +`
                    </button>
                `;
            }
            componentHandler.upgradeDom();
        }
        return _btn
    }
})