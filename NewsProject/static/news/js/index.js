var currentCid = 0; // 当前分类 id
var cur_page = 0; // 当前页
var total_page = 1;  // 总页数
var data_querying = true;   // 是否正在向后台获取数据


$(function () {
    // 初始化vue对象
    vue_list_con = new Vue({
        el: ".list_con",
        delimiters: ['[[', ']]'],  // 将vue语法中的{{}}换成[[]]
        data: {
            news_list: []
        }
    });
    updateNewsData();
    // 首页分类切换
    $('.menu li').click(function () {
        var clickCid = $(this).attr('data-cid');
        $('.menu li').each(function () {
            $(this).removeClass('active')
        });
        $(this).addClass('active');

        if (clickCid != currentCid) {
            // TODO 去加载新闻数据
            currentCid = clickCid;
            cur_page = 0;
            updateNewsData();

        }
    });

    //页面滚动加载相关
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        if ((canScrollHeight - nowScroll) < 100  && data_querying) {
            // TODO 判断页数，去更新新闻数据
            updateNewsData()
        }
    })
});

function updateNewsData() {
    // TODO 更新新闻数据
    data_querying = false;
    // ajax请求
    $.get("newslist", {
        "page": cur_page+1,
        // 分类编号
        "category_id": currentCid
    }, function (data) {
        // 第一次加载某个分类应该进行赋值
        // 分类加载, 进行拼接
        if(cur_page==0){
            // 第一次加载分类
            vue_list_con.news_list = data.news_list;
        }
        else {
            // 非第一次加载, 进行拼接
            vue_list_con.news_list = vue_list_con.news_list.concat(data.news_list);
        }
        cur_page = data.page;
        data_querying = true;
    });
}
