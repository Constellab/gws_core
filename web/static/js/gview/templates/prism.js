new GViewTemplate({
    class: "gview:action",
    render: function (data) {
        var target = data.target
        console.log(target)
        console.log(document.querySelector(target))
        var gviewObj = document.querySelector(target).userData.gview
        gviewObj.render(data)
    }
})