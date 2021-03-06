/**
 * Created by kimkkikki on 2017. 3. 24..
 */

$('#slot-guide-button').click(function () {
    $('#slot-guide-modal').modal('show');
});

function share_facebook(){
    waitMe($('#slot-modal'));
    html2canvas(document.getElementById('slot-result-detail'), {
        useCORS: true,
        onrendered: function(canvas) {
            var image = canvas.toDataURL('image/jpeg', 0.9);
            ga('send', 'event', {
                eventCategory: 'ajax',
                eventAction: '/apis/upload/facebook'
            });

            $.ajax({
                url:'/apis/upload',
                headers: {
                    'Content-Type':'application/json'
                },
                data: JSON.stringify({
                    'image': image
                }),
                type:'POST',
                success:function(data){
                    console.log(data);
                    $('#slot-modal').waitMe('hide');
                    snsShare('facebook', data, '2017대선닷컴 후보 돌림판 당첨!');
                    $('#honor_nickname').removeAttr('disabled');
                    $('#add_honor').removeAttr('disabled');
                },
                error: function(data, status, err) {
                    $('#slot-modal').waitMe('hide');
                    console.log(err);
                }
            });
        }
    });
}

function share_kakaotalk(){
    waitMe($('#slot-modal'));
    html2canvas(document.getElementById('slot-result-detail'), {
        useCORS: true,
        onrendered: function(canvas) {
            var image = canvas.toDataURL('image/jpeg', 0.9);
            ga('send', 'event', {
                eventCategory: 'ajax',
                eventAction: '/apis/upload/kakao'
            });

            $.ajax({
                url:'/apis/upload',
                headers: {
                    'Content-Type':'application/json'
                },
                data: JSON.stringify({
                    'image': image
                }),
                type:'POST',
                success:function(data){
                    console.log(data);
                    $('#slot-modal').waitMe('hide');
                    snsShare('kakaotalk', data, '대선잿팟');
                    $('#honor_nickname').removeAttr('disabled');
                    $('#add_honor').removeAttr('disabled');
                },
                error: function(data, status, err) {
                    $('#slot-modal').waitMe('hide');
                    console.log(err);
                }
            });
        }
   });
}

var slot_count = 0;
var slot_result_count;
var slot_result_candidate;
var machine1 = $("#slot-machine-1").slotMachine({
                active	: Math.floor(Math.random() * 10),
                delay	: 500
            });
var machine2 = $("#slot-machine-2").slotMachine({
                active	: Math.floor(Math.random() * 10),
                delay	: 500
            });
var machine3 = $("#slot-machine-3").slotMachine({
                active	: Math.floor(Math.random() * 10),
                delay	: 500
            });

var result_1, result_2, result_3;
var slotModalCount = $('#slot-machine-count');
function onComplete(active){
    switch(this.element[0].id){
        case 'slot-machine-1':
            result_1 = active;
            break;
        case 'slot-machine-2':
            result_2 = active;
            break;
        case 'slot-machine-3':
            slot_count++;
            slotModalCount.html('총 ' + slot_count + '번 돌리셨습니다');
            result_3 = active;

            slotStart.prop('disabled', false);
            if (result_1 === result_2 && result_2 === result_3) {
                waitMe($('#slot'));
                slot_result_candidate = slot_candidates[result_1];
                slot_result_count = slot_count;
                ga('send', 'event', {
                    eventCategory: 'ajax',
                    eventAction: '/slot'
                });

                $.ajax({
                        url: '/slot',
                        headers: {
                            'Content-Type':'application/json'
                        },
                        async: true,
                        type: 'POST',
                        data: JSON.stringify({
                            'type': 'slot',
                            'candidate': slot_result_candidate,
                            'count': slot_result_count
                        }),
                        success: function(data) {
                            $('#slot-result').html(data);
                            $('#slot-modal').modal('show');
                            slot_count = 0;
                            $('#slot').waitMe('hide');
                        },
                        error: function(data, status, err) {
                            console.log(err);
                            $('#slot').waitMe('hide');
                        }
                    });
            } else {
                var messages = ['까비 다시 도전해보세요', '후보 고르기 쉽지 않죠. 다시고고!', '힘내세요. 다시 도전!', '슬슬 포기단계? 힘내서 고고!', '확률은 확률일 뿐. 다시 도전!', 'ㅠㅠ', '까비요.'];
                slotModalCount.attr('data-original-title', messages[Math.floor((Math.random() * 8))])
                  .tooltip('show');
            }
            break;
    }
}

var isLoadHonor = false;
$('#slot-honor-button').click(function () {
    if (!isLoadHonor) {
        waitMe($('#slot'));
        ga('send', 'event', {
            eventCategory: 'ajax',
            eventAction: '/slot/honor'
        });

        $.ajax({
                url: '/slot/honor',
                headers: {
                    'Content-Type':'application/json'
                },
                type: 'GET',
                success: function(data) {
                    $('#slot-honor-result').html(data);
                    $('#slot-honor-modal').modal('show');
                    isLoadHonor = true;
                    $('#slot').waitMe('hide');
                },
                error: function(data, status, err) {
                    console.log(err);
                    $('#slot').waitMe('hide');
                }
            });
    } else {
        $('#slot-honor-modal').modal('show');
    }
});

var slotStart = $('#slot-start');

slotStart.click(function() {
    slotStart.prop('disabled', true);
    slotStart.text('다시돌려!');
    machine1.shuffle(5, onComplete);
    machine2.shuffle(10, onComplete);
    machine3.shuffle(15, onComplete);
    $('#slot-machine-count').tooltip('hide');
});

function check() {
    if ($('#honor_nickname')[0].disabled === true) {
        $('#add-honor-form').attr('data-original-title', '소셜 공유 후에 명예의 전당에 등록하실 수 있습니다').tooltip('show');
    } else {
        $('#add-honor-form').removeAttr('data-original-title');
    }
}

$(document).ready(function(){
    $('#add_honor').click(function () {
        var nickname = $('#honor_nickname').val();
        if (nickname === '') {
            alert('닉네임을 입력해야 합니다.')
        } else{
            var addHonorModal = $('#slot-add-honor-modal');
            waitMe(addHonorModal);
            ga('send', 'event', {
                eventCategory: 'ajax',
                eventAction: '/apis/slot',
                eventLabel: 'POST'
            });

            $.ajax({
                url: '/apis/slot',
                headers: {
                    'Content-Type':'application/json'
                },
                async: true,
                type: 'POST',
                data: JSON.stringify({
                    'candidate': slot_result_candidate,
                    'count': slot_result_count,
                    'nickname': nickname
                }),
                success: function(data) {
                    alert(data.message);
                    addHonorModal.waitMe('hide');
                    addHonorModal.modal('toggle');
                    $('#slot-modal').modal('toggle');
                    // addHonorModal.modal('hide');
                    // $('#slot-modal').modal('hide');
                },
                error: function(data, status, err) {
                    console.log(err);
                    addHonorModal.waitMe('hide');
                }
            });
        }
    });
});