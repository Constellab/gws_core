new GViewTemplate({
    class: "gview:card",
    render: function (data) {
        data.style = data.style || ""
        data.title = data.title || ""
        data.body = data.body || ""
        return `
            <div class="card ` + data.style + `">
                <div class="card-header">
                    ` + data.title + `
                </div>
                <div class="card-body">
                    ` + data.body + `
                </div>
            </div>
        `;
    }
})

// new GViewTemplate({
//     class: "gview:card-tasks",
//     render: function (data){
//         var header = ''
//         for(var val of data.header){
//             header += '<th>'+val+'</th>'
//         }

//         for(var row of data.body){
//             rowText += `
//                 <td>
//                     <div class="form-check">
//                         <label class="form-check-label">
//                             <input class="form-check-input" type="checkbox" value="">
//                             <span class="form-check-sign">
//                                 <span class="check"></span>
//                             </span>
//                         </label>
//                     </div>
//                 </td>
//             `;

//             for(var val of row){
//                 rowText += `
//                     <td>
//                         <p class="title">`+val.title+`</p>
//                         <p class="text-muted">`+val.description+`</p>
//                     </td>
//                 `;
//             }
            
//             rowText += `
//                 <td class="td-actions text-right">
//                     <button type="button" rel="tooltip" title="" class="btn btn-link" data-original-title="Edit Task">
//                         <i class="tim-icons icon-pencil"></i>
//                     </button>
//                 </td>
//             `;

//             rowText = "<tr>" + rowText + "</tr>";
//         }
        
//         data.style = data.style || ""

//         return `
//             <div class="card card-tasks `+data.style+`">
//                 <div class="card-header">
//                     <h6 class="title d-inline">`+data.title+`</h6>
//                     <p class="card-category d-inline">`+data.subtitle+`</p>
//                     <div class="dropdown">
//                         <button type="button" class="btn btn-link dropdown-toggle btn-icon" data-toggle="dropdown">
//                             <i class="tim-icons icon-settings-gear-63"></i>
//                         </button>
//                         <div class="dropdown-menu dropdown-menu-right" aria-labelledby="dropdownMenuLink">
//                         <a class="dropdown-item" href="#pablo">Action</a>
//                         <a class="dropdown-item" href="#pablo">Another action</a>
//                         <a class="dropdown-item" href="#pablo">Something else</a>
//                     </div>
//                 </div>
            
//                 <div class="card-body">
//                     <div class="table-full-width table-responsive">
//                         <table class="table">
//                             <tbody>
//                                 ` + rowText + `
//                             </tbody>
//                         </table>
//                     </div>
//                 <div>
//             </div>
//         `;
//     }
// })