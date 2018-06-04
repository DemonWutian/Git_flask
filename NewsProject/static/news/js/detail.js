function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function(){

    // 收藏
    $(".collection").click(function () {
        // 页面没有news_id, 需要手动添加一个隐藏标签, 从视图中传递到模板中
        $.post("/collect/"+$("#news_id").val(), {
            "csrf_token": $("#csrf_token").val()
        }, function (data) {
            if(data.result==2){
                // 用户未登录, 弹出登陆框
                $('.login_btn').click();
            }
            else if(data.result==3){
                // 收藏成功
                $(".collection").hide();
                $(".collected").show();
            }
        });

    });

    // 取消收藏
    $(".collected").click(function () {
        $.post("/collect/"+$("#news_id").val(), {
            "csrf_token": $("#csrf_token").val(),
            "action": 2
        }, function (data) {
            if(data.result==3){
                // 取消收藏成功
                $(".collection").show();
                $(".collected").hide();
            }
        })

    });

        // 评论提交
    $(".comment_form").submit(function (e) {
        e.preventDefault();
        $.post("/comment/add", {
            "news_id": $("#news_id").val(),
            "msg": $("#msg").val(),
            "csrf_token": $("#csrf_token").val()
        }, function (data) {
            if(data.result==1){
                alert("请输入评论内容")
            }
            else if(data.result==4){
                $("#msg").val("");
                $(".comment").text(data.comment_count);
                $(".comment_count>span").text(data.comment_count)
                get_comment_list();
            }
        });

    });

    $('.comment_list_con').delegate('a,input','click',function(){

        var sHandler = $(this).prop('class');

        if(sHandler.indexOf('comment_reply')>=0)
        {
            $(this).next().toggle();
        }

        if(sHandler.indexOf('reply_cancel')>=0)
        {
            $(this).parent().toggle();
        }

        if(sHandler.indexOf('comment_up')>=0)
        {
            var $this = $(this);
            if(sHandler.indexOf('has_comment_up')>=0)
            {
                // 如果当前该评论已经是点赞状态，再次点击会进行到此代码块内，代表要取消点赞
                $this.removeClass('has_comment_up')
            }else {
                $this.addClass('has_comment_up')
            }
        }

        if(sHandler.indexOf('reply_sub')>=0)
        {
            alert('回复评论')
        }
    });



        // 关注当前新闻作者
    $(".focus").click(function () {

    });

    // 取消关注当前新闻作者
    $(".focused").click(function () {

    });

    // 获取评论数据
    vue_comment_list = new Vue({
        el: ".comment_list_con",
        delimiters: ['[[', ']]'],  // 将vue语法中的{{}}换成[[]]
        data: {
            comment_list: []
        }
    });
    get_comment_list();
});




function get_comment_list() {
    $.get("/comment/list/"+$("#news_id").val(), function (data) {
            vue_comment_list.comment_list=data.comment_list
        }
    )
}
