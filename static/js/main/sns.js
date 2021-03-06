/**
 * Created by kimkkikki on 2017. 3. 24..
 */

Kakao.init('17c8317e213251d5ed0578e27ad3b8e9');

window.twttr = (function(d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0],
    t = window.twttr || {};
  if (d.getElementById(id)) return t;
  js = d.createElement(s);
  js.id = id;
  js.src = "https://platform.twitter.com/widgets.js";
  fjs.parentNode.insertBefore(js, fjs);

  t._e = [];
  t.ready = function(f) {
    t._e.push(f);
  };

  return t;
}(document, "script", "twitter-wjs"));

function snsShare(sns, imageUrl, title) {
    if (sns == 'facebook') {
        FB.ui({
            method: 'feed',
            picture : imageUrl,
            name: title,
            caption: '2017대선닷컴',
            description: '대선후보에서 잘맞는 후보를 찾았습니다! 이 후보랑 잘 맞으시네요 ㅎㅎ',
            link: 'https://2017daesun.com'
        }, function(response){
            if (response && !response.error_code) {
                console.log("Facebook Share Success : " + JSON.stringify(response));
            } else {
                console.log("Facebook Share Failure : " + JSON.stringify(response));
            }
        });

    } else if (sns == 'twitter') {
        //TODO: 이미지 공유 방법 모르겠음..
        var windowOptions = 'scrollbars=yes,resizable=yes,toolbar=no,location=yes',
            width = 550,
            height = 420;

        window.open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(title) + '&url=' + encodeURIComponent(imageUrl),
            'intent', windowOptions + ',width=' + width + ',height=' + height);

    } else if (sns == 'kakaotalk') {
        console.log(sns);
        Kakao.Link.sendTalkLink({
            label: title,
            image: {
                src: imageUrl,
                width: '300',
                height: '200'
            },
            webButton: {
                text: '2017대선닷컴',
                url: 'https://2017daesun.com'
            },
            fail: function(){
                alert('카카오톡 앱이 설치되어 있는 모바일 기기에서만 전송 가능합니다.');
                console.log('fail share kakaotalk');
            }
        });
    } else {
        alert('지원하지 않는 SNS 입니다');
        console.log(sns);
    }
}
