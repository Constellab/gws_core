new GViewTemplate({
    class: "gview:sidebar-btn",
    render: function (data) {
        return `
            <li class="active">
                <a href="`+ data.url + `" target="">
                    <i class="`+ data.icon + `"></i>
                    <p>`+ data.name + `</p>
                </a>
            </li>
        `;
    }
})
