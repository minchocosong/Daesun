$(function() {
    var before = null;
    $('#rating-toggle').change(function() {
        var description = $('#rating-description');
        var is_rating = $(this).prop('checked');
        var template = $('#rating-template');
        var temp;
        if (is_rating) {
            description.html("리얼미터가 조사한 여론조사 결과입니다. 자세한 내용은 리얼미터 홈페이지를 참고하세요");
            if (before != null) {
                temp = template.html();
                template.html(before);
                before = temp;
            }
        } else {
            description.html("운빨 지지율은 2017대선닷컴의 럭키박스를 이용한 방문자 결과를 기반으로 계산되었습니다.<br>위의 결과는 철저히 랜덤함수에 의한 결과의 합임을 명심해주세요. 오해금지!");
            if (before == null) {
                waitMe($('#rating'));
                $.ajax({
                    url: '/rating',
                    headers: {
                        'Content-Type':'application/json'
                    },
                    type: 'POST',
                    data: JSON.stringify({
                            'type': 'lucky'
                        }),
                    success: function(data) {
                        before = template.html();
                        template.html(data);
                        $('#rating').waitMe('hide');
                        page = 1;
                    },
                    error: function() {
                        alert('우주의기운 지지율을 가져오는데 실패하였습니다');
                        $('#rating').waitMe('hide');
                    }
                });
            } else {
                temp = template.html();
                template.html(before);
                before = temp;
            }
        }
    })
});

// 지지율 차트
var isLoadRatingChart = false;
$('#rating-graph-button').click(function() {
    if (!isLoadRatingChart) {
        waitMe($('#rating-modal'));
        $.ajax({
            url: '/apis/rating',
            headers: {
                'Content-Type':'application/json'
            },
            async: true,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                var result_list = [['x'], ['문재인'], ['안철수'], ['황교안'], ['남경필'], ['안희정'], ['이재명'], ['유승민']];
                for (var i = 0; i < data.length; i++) {
                    var obj = data[i];
                    if (!result_list[0].includes(obj.date)) {
                        result_list[0].push(obj.date);
                    }

                    switch (obj.candidate) {
                        case '문재인':
                            result_list[1].push(obj.rating);
                            break;
                        case '안철수':
                            result_list[2].push(obj.rating);
                            break;
                        case '황교안':
                            result_list[3].push(obj.rating);
                            break;
                        case '남경필':
                            result_list[4].push(obj.rating);
                            break;
                        case '안희정':
                            result_list[5].push(obj.rating);
                            break;
                        case '이재명':
                            result_list[6].push(obj.rating);
                            break;
                        case '유승민':
                            result_list[7].push(obj.rating);
                            break;
                    }
                }

                c3.generate({
                    bindto: '#ratingChart',
                    data: {
                        x: 'x',
                        columns: result_list
                    },
                    axis: {
                        x: {
                            type: 'timeseries',
                            tick: {
                                format: '%Y-%m-%d'
                            }
                        }
                    }
                });
                $('#rating-modal').waitMe('hide');
                isLoadRatingChart = true;
            },
            error: function(data, status, err) {
                console.log(err);
                $('#rating-modal').waitMe('hide');
            }
        });
    }
});