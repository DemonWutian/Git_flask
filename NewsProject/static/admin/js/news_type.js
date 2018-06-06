function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
var sId = 0;
$(function () {
    var $a = $('.edit');
    var $add = $('.addtype');
    var $pop = $('.pop_con');
    var $cancel = $('.cancel');
    var $confirm = $('.confirm');
    var $error = $('.error_tip');
    var $input = $('.input_txt3');
    var sHandler = 'edit';


    vue_list_con = new Vue({
        el: ".common_table",
        delimiters: ['[[', ']]'],
        data: {
            category_list: []
        },
        methods: {
            add: function () {
                sHandler = 'add';
                $pop.find('h3').html('新增分类');
                $input.val('');
                $pop.show();
            },
            edit: function (event) {
                $this = $(event.target);
                sHandler = 'edit';
                sId = $this.parent().siblings().eq(0).html();
                $pop.find('h3').html('修改分类');
                $pop.find('.input_txt3').val($this.parent().prev().html());
                $pop.show();
            },
            delete: function (event) {
                //
            }
        }
    });
    get_category_list();



    $cancel.click(function () {
        $pop.hide();
        $error.hide();
    });

    $input.click(function () {
        $error.hide();
    });

    $confirm.click(function () {
        if (sHandler == 'edit') {
            var sVal = $input.val();
            if (sVal == '') {
                $error.html('输入框不能为空').show();
                return;
            }
            // 发起edit post请求
            $.post("/admin/news_type_edit", {
                "name": sVal,
                "csrf_token": $("#csrf_token").val(),
                "id": sId
            }, function (data) {
                if(data.result==2){
                    $error.html("此分类名称已经存在!").show();
                }
                else if(data.result==1){
                    get_category_list();
                    $cancel.click()
                }
            })

        }
        else {
            var sVal = $input.val();
            if (sVal == '') {
                $error.html('输入框不能为空').show();
                return;
            }
            // 发起add post请求
            $.post("/admin/news_type_add", {
                "name": sVal,
                "csrf_token": $("#csrf_token").val()
            }, function (data) {
                if(data.result==1){
                    get_category_list();
                    $cancel.click();
                }
                else if(data.result==2){
                    $error.html("此分类名称已经存在!").show();
                }
            });
        }

    })
});
function get_category_list() {
    $.get("/admin/news_type_list", function (data) {
        vue_list_con.category_list = data.category_list
    });

}