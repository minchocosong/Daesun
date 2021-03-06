from apis.models import Scraps, Keywords, Pledge, ApprovalRating, LoveOrHate, IssueKeyword, CheeringMessage, LuckyRating, Calendar, Honor, Candidate
from django.http import HttpResponse, Http404
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from django.db.models import Q, Case, When, Sum, F, Avg, Count
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import caches
from django.views.decorators.cache import cache_page
import json
import uuid
from .util import hangle, constellation, blood_type, zodiac
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from operator import itemgetter
import requests
import twitter
import pytz
import re
import base64
import random
from google.cloud import storage
import os
from django.conf import settings


def get_candidates():
    cache = caches['default']
    candidates = cache.get('candidates', None)
    if candidates is None:
        candidates = Candidate.objects.filter(running=True).order_by('candidate')
        cache.set('candidates', candidates)
    return candidates


def get_candidates_query_list():
    candidates = get_candidates()
    q_list = []
    for candidate in candidates:
        q_list.append(Q(title__contains=candidate.candidate))

    query = q_list.pop()
    for item in q_list:
        query |= item

    return query


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def save_lucky_rating(candidate, lucky_type, lucky_input, score):
    if os.getenv('GAE_INSTANCE'):
        if score is not None:
            lucky_rating = LuckyRating(candidate=candidate, type=lucky_type, input=lucky_input, score=score)
        else:
            lucky_rating = LuckyRating(candidate=candidate, type=lucky_type, input=lucky_input)
        lucky_rating.save()


def get_news_list(request):
    body = JSONParser().parse(request)
    request_keyword = body.get('keywords', None)
    keywords = request_keyword.split(' ')
    q_list = []
    for keyword in keywords:
        if keyword != 'ALL':
            q_list.append(Q(title__contains=keyword))

    query = q_list.pop()
    for item in q_list:
        query &= item

    news_list = Scraps.objects.filter(query).order_by('-created_at')[0:10]

    return news_list


@cache_page(60 * 10)
def cp_group(request):
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    if start_date is not None and end_date is not None:
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d') + timedelta(days=1)
        candidate_q_list = Q(created_at__range=[start, end]) & get_candidates_query_list()
    else:
        candidate_q_list = get_candidates_query_list()

    group_list = Scraps.objects.filter(Q(created_at__gte=datetime.now() - timedelta(days=30)) & candidate_q_list).values('cp').annotate(
        moon=Count(Case(When(title__contains='문재인', then=1))),
        ahn=Count(Case(When(title__contains='안철수', then=1))),
        you=Count(Case(When(title__contains='유승민', then=1))),
        sim=Count(Case(When(title__contains='심상정', then=1))),
        hong=Count(Case(When(title__contains='홍준표', then=1))),
    )

    return JSONResponse(list(group_list))


@cache_page(60 * 10)
def cp_daily(request):
    cp = request.GET.get('cp', None)

    if cp is not None:
        candidate_q_list = Q(created_at__gte=datetime.now() - timedelta(days=30)) & Q(cp=cp) & get_candidates_query_list()
    else:
        candidate_q_list = Q(created_at__gte=datetime.now() - timedelta(days=30)) & get_candidates_query_list()

    daily_list = Scraps.objects.filter(candidate_q_list).extra({'date': 'date(created_at)'}).values(
        'date').annotate(
        moon=Count(Case(When(title__contains='문재인', then=1))),
        ahn=Count(Case(When(title__contains='안철수', then=1))),
        you=Count(Case(When(title__contains='유승민', then=1))),
        sim=Count(Case(When(title__contains='심상정', then=1))),
        hong=Count(Case(When(title__contains='홍준표', then=1))),
    )

    return JSONResponse(list(daily_list))


def get_shop():
    results = []

    for candidate in get_candidates():
        url = "https://openapi.naver.com/v1/search/book_adv.json?d_titl=" + candidate.candidate +\
              "&d_auth=" + candidate.candidate + "&sort=date&d_dafr=20150101&d_dato=20171231"

        response = requests.get(url, headers={'X-Naver-Client-Id': 'cC0cf4zyUuLFmj_kKUum',
                                              'X-Naver-Client-Secret': 'EYop6SBs44'})
        result = response.json()

        if 'items' in result:
            for obj in result['items']:
                obj['image'] = obj['image'].replace('type=m1&', 'type=m5&')
                obj['title'] = obj['title'].split('(')[0]
                results.append(obj)

    results = sorted(results, key=itemgetter('pubdate'), reverse=True)
    return results


@cache_page(60 * 10)
def shop(request):
    if request.method == 'GET':
        return JSONResponse(get_shop())


def pledge_rank_list():
    pledges = Pledge.objects.annotate(score=Sum(F('like') - F('unlike'))).order_by('-score')[0:10]
    return list(pledges.values())


@cache_page(60 * 10)
def pledge_rank_api(request):
    if request.method == 'GET':
        return JSONResponse(pledge_rank_list())


def pledge_get():
    cache = caches['default']
    evaluate_token = str(uuid.uuid4())
    cache_key = 'pledge_evaluate|' + evaluate_token

    pledge_obj = Pledge.objects.all().order_by('updated')[0:10]
    pledges = list(pledge_obj.values())
    print(pledges)

    data = {"token": evaluate_token, "list": pledges}
    # 10개 공약 순서대로 누군지 저장해야함
    cache.set(cache_key, json.dumps(data, cls=DjangoJSONEncoder), timeout=600)

    return data


def pledge_post(request):
    cache = caches['default']
    body = JSONParser().parse(request)
    token = body.get('token', None)
    result_list = body.get('list', None)
    cache_key = 'pledge_evaluate|' + token
    cache_data = cache.get(cache_key)
    cache.delete(cache_key)

    print(cache_data)

    if cache_data is None:
        # Expire
        return JSONResponse({'message': '10분 이내에 입력해야 합니다'}, status=400)

    cache_data = json.loads(cache_data)

    candidate_list = cache_data['list']
    count_dict = {'문재인': 0, '안철수': 0, '이재명': 0, '유승민': 0, '안희정': 0, '심상정': 0, '남경필': 0, '홍준표': 0}
    title_dict = {'문재인': [], '안철수': [], '이재명': [], '유승민': [], '안희정': [], '심상정': [], '남경필': [], '홍준표': []}

    for i, result in enumerate(result_list):
        if result == 1 or result == '1':
            Pledge.objects.filter(id=candidate_list[i].get('id')).update(like=F('like') + 1, updated=datetime.now())
            count_dict[candidate_list[i].get('candidate')] += 1
            title_dict[candidate_list[i].get('candidate')].append(candidate_list[i].get('title'))
        elif result == -1 or result == '-1':
            Pledge.objects.filter(id=candidate_list[i].get('id')).update(unlike=F('unlike') + 1,
                                                                         updated=datetime.now())
            count_dict[candidate_list[i].get('candidate')] -= 1

    result_list = [{'candidate': '문재인', 'count': count_dict['문재인'], 'titles': title_dict['문재인']},
                   {'candidate': '안철수', 'count': count_dict['안철수'], 'titles': title_dict['안철수']},
                   {'candidate': '이재명', 'count': count_dict['이재명'], 'titles': title_dict['이재명']},
                   {'candidate': '유승민', 'count': count_dict['유승민'], 'titles': title_dict['유승민']},
                   {'candidate': '안희정', 'count': count_dict['안희정'], 'titles': title_dict['안희정']},
                   {'candidate': '심상정', 'count': count_dict['심상정'], 'titles': title_dict['심상정']},
                   {'candidate': '남경필', 'count': count_dict['남경필'], 'titles': title_dict['남경필']},
                   {'candidate': '홍준표', 'count': count_dict['홍준표'], 'titles': title_dict['홍준표']},
                   ]
    result_list = sorted(result_list, key=itemgetter('count'), reverse=True)

    return result_list


@csrf_exempt
def pledge(request):
    if request.method == 'GET':
        return JSONResponse(pledge_get())

    elif request.method == 'POST':
        return JSONResponse(pledge_post(request))


def lucky_rating_count():
    lucky_count = len(LuckyRating.objects.all().annotate(count=Count('input', distinct=True)))
    return lucky_count


def lucky_rating_list(result_type):
    candidates = get_candidates()
    q_list = []
    for candidate in candidates:
        q_list.append(Q(candidate=candidate.candidate))

    query = q_list.pop()
    for item in q_list:
        query |= item

    if result_type == 'all':
        lucky_ratings = LuckyRating.objects.filter(query).values('candidate', 'type').annotate(count=Count('candidate')).order_by('-count')

        result_list = []
        for lucky in lucky_ratings:
            has_candidate = False
            for result in result_list:
                if lucky['candidate'] == result['candidate']:
                    has_candidate = True
                    if lucky['type'] == 'star':
                        result['count'] += lucky['count'] * 3
                    elif lucky['type'] == 'name':
                        result['count'] += lucky['count'] * 10
                    elif lucky['type'] == 'zodiac':
                        result['count'] += lucky['count'] * 3
                    elif lucky['type'] == 'blood':
                        result['count'] += lucky['count'] * 1
                    elif lucky['type'] == 'slot':
                        result['count'] += lucky['count'] * 100
                    elif lucky['type'] == 'total':
                        result['count'] += lucky['count'] * 50
                    break

            if not has_candidate:
                if lucky['type'] == 'star':
                    lucky['count'] *= 3
                elif lucky['type'] == 'name':
                    lucky['count'] *= 10
                elif lucky['type'] == 'zodiac':
                    lucky['count'] *= 3
                elif lucky['type'] == 'blood':
                    lucky['count'] *= 1
                elif lucky['type'] == 'slot':
                    lucky['count'] *= 100
                elif lucky['type'] == 'total':
                    lucky['count'] *= 50
                result_list.append(lucky)

        result_list = sorted(result_list, key=itemgetter('count'), reverse=True)
        return result_list
    else:
        lucky_ratings = LuckyRating.objects.filter(query).values('candidate', 'type').annotate(count=Count('candidate')).order_by('-count')
        result_list = list(lucky_ratings)

        for result in result_list:
            if result['type'] == 'star':
                result['score'] = result['count'] * 3
            elif result['type'] == 'name':
                result['score'] = result['count'] * 10
            elif result['type'] == 'zodiac':
                result['score'] = result['count'] * 3
            elif result['type'] == 'blood':
                result['score'] = result['count'] * 1
            elif result['type'] == 'slot':
                result['score'] = result['count'] * 100
            elif result['type'] == 'total':
                result['score'] = result['count'] * 50

        result_list = sorted(result_list, key=itemgetter('count'), reverse=True)
        return result_list


def slot_honor_list():
    honor_list = Honor.objects.all().order_by('-count').values('candidate', 'count', 'name', 'created')[0:30]
    return list(honor_list)


def slot_honor_api(request):
    if request.method == 'GET':
        return JSONResponse(slot_honor_list())
    else:
        body = JSONParser().parse(request)
        isExist = Honor.objects.filter(candidate=body.get('candidate'), count=body.get('count'), name=body.get('nickname'))

        if len(isExist) != 0:
            return JSONResponse({'message': '이미 등록되었습니다.'}, status=200)

        honor = Honor(candidate=body.get('candidate'), count=body.get('count'), name=body.get('nickname'))
        honor.save()
        return JSONResponse({'message': '등록되었습니다.'}, status=200)


def approval_rating_list(cp, is_last):
    if is_last:
        last = ApprovalRating.objects.latest('date').date
        approval_ratings = ApprovalRating.objects.filter(date=last).values('candidate', 'date')\
            .annotate(rating=Avg(F('rating'))).order_by('-rating')
    else:
        if cp is None:
            approval_ratings = ApprovalRating.objects.filter(type=1, date__gte=datetime.now() - timedelta(days=30)) \
                .values('candidate', 'date').annotate(rating=Avg(F('rating'))).order_by('date')
        else:
            approval_ratings = ApprovalRating.objects.filter(type=1, date__gte=datetime.now() - timedelta(days=30), cp=cp) \
                .values('candidate', 'date').annotate(rating=Avg(F('rating'))).order_by('date')

    return list(approval_ratings)


@cache_page(60 * 10)
@csrf_exempt
def approval_rating(request):
    return JSONResponse(approval_rating_list(request.GET.get('cp', None), False))


@csrf_exempt
def name_chemistry(request):
    if request.method == 'GET':
        name = request.GET.get('name', None)
    else:
        body = JSONParser().parse(request)
        name = body.get('name', None)

    if name is None:
        return JSONResponse({'message': 'param is missing'}, status=400)

    result_list = []
    for candidate in get_candidates():
        score_to = hangle.name_chemistry(name, candidate.candidate)
        score_from = hangle.name_chemistry(candidate.candidate, name)
        result_list.append({'candidate': candidate.candidate, 'score_to': score_to, 'score_from': score_from, 'score': score_to + score_from})

    if len(result_list) > 0:
        result_list = sorted(result_list, key=itemgetter('score'), reverse=True)
        save_lucky_rating(result_list[0]['candidate'], 'name', name, None)

    return JSONResponse({'list': result_list})


def lucky_name(request):
    if request.method == 'GET':
        name = request.GET.get('name', None)
    else:
        body = JSONParser().parse(request)
        name = body.get('name', None)
    print(name)
    result_list = []
    score, best_to, best_from, best_to_name, best_from_name = 0, [], [], [], []
    for candidate in get_candidates():
        score_to, score_to_list, name_to_list = hangle.name_chemistry(name, candidate.candidate)
        score_from, score_from_list, name_from_list = hangle.name_chemistry(candidate.candidate, name)
        result_list.append({'candidate': candidate.candidate, 'score_to': score_to, 'score_from': score_from,
                            'score': (score_to + score_from) / 2})
        if score < score_to + score_from:
            best_to, best_from, best_to_name, best_from_name = score_to_list, score_from_list, name_to_list, name_from_list
            score = score_to + score_from

    if len(result_list) > 0:
        result_list = sorted(result_list, key=itemgetter('score'), reverse=True)
        save_lucky_rating(result_list[0]['candidate'], 'name', name, result_list[0]['score'])

    i, j, length, to_nodes, from_nodes = 0, 0, len(best_to), [], []

    for name_one in best_to_name:
        to_nodes.append({"id": 99 - j, "label": name_one, "level": length, 'color': {'border': "#ffffff"}})
        j += 1

    for item in best_to:
        for score in item:
            if length == 1:
                to_nodes.append({"id": i, "label": score, "level": length-1, 'font': {'color': "#ffffff"}, "color": "#fec503"})
            else:
                to_nodes.append({"id": i, "label": score, "level": length - 1})
            i += 1
        length -= 1

    i, j, length = 0, 0, len(best_from)

    for name_one in best_from_name:
        from_nodes.append({"id": 99 - j, "label": name_one, "level": length, 'color': {'border': "#ffffff"}})
        j += 1

    for item in best_from:
        for score in item:
            if length == 1:
                from_nodes.append({"id": i, "label": score, "level": length-1, 'font': {'color': "#ffffff"}, "color": "#fec503"})
            else:
                from_nodes.append({"id": i, "label": score, "level": length - 1})
            i += 1
        length -= 1

    rank = LuckyRating.objects.filter(type='total', score__gt=result_list[0]['score']).count() + 1

    return {'name_length': len(name)+3, 'name': name, 'result': result_list[0], 'list': result_list, 'to_nodes': to_nodes, 'from_nodes': from_nodes, 'rank': rank}


@api_view(['GET'])
def timeline(req):
    param = int(req.GET.get('param', 1))

    start_date = datetime.now() - timedelta(hours=param * 3)
    end_date = start_date + timedelta(hours=3)

    date_group_list = Keywords.objects.values('created_at').annotate(count=Count('created_at')).filter(
        created_at__gte=start_date).filter(created_at__lte=end_date).order_by('-created_at')
    result_list = []
    for data_group in date_group_list:
        result_inner = {}
        candidate_list = Keywords.objects.values('candidate').annotate(count=Count('candidate')).filter(
            created_at__contains=data_group['created_at'])
        result_data_list = []

        for c in candidate_list:
            inner = {}
            keyword_list = []
            candidate_keyword_list = Keywords.objects.values('candidate', 'keyword', 'count').filter(
                candidate__contains=c['candidate']).filter(created_at__contains=data_group['created_at'])
            for ck in candidate_keyword_list:
                inner_keyword = {'keyword': ck['keyword'], 'count': ck['count']}
                scraps = [{'title': scraps['title'], 'link': scraps['link'], 'cp': scraps['cp'],
                           'created_at': scraps['created_at'].strftime('%Y-%m-%d %H:%M:%S')} for scraps in
                          Scraps.objects.values('title', 'link', 'cp', 'created_at').order_by('-created_at').
                          filter(title__contains=ck['candidate']).filter(title__contains=ck['keyword'])[:5]]
                inner_keyword['news'] = scraps
                keyword_list.append(inner_keyword)

            inner['candidate'] = c['candidate']
            inner['keywords'] = keyword_list
            result_data_list.append(inner)

        result_inner['created_at'] = data_group['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        result_inner['data'] = result_data_list
        result_list.append(result_inner)

    return JSONResponse(list(result_list))


@api_view(['GET'])
def love_test(request):
    if request.method == 'GET':
        candidate_dict = {'문재인': 1, '안희정': 2, '이재명': 3, '안철수': 4, '유승민': 5, '황교안': 6, '남경필': 7}
        result_list = []
        result_db_list = LoveOrHate.objects.values('speaker', 'target').annotate(s_cnt=Count('speaker'),
                                                                                 t_cnt=Count('target'))
        speaker, target, count, arrows = result_db_list[0]['speaker'], result_db_list[0]['target'], result_db_list[0][
            't_cnt'], 'to'
        for result in result_db_list:
            if speaker != result['speaker']:
                result_list.append({'from': candidate_dict[speaker], 'to': candidate_dict[target],
                                    'arrows': arrows})
                speaker, target, count = result['speaker'], result['target'], result['t_cnt']

            if count < result['t_cnt']:
                count, target = result['t_cnt'], result['target']
                if count > 20:
                    arrows = {'to': {'scaleFactor': '2'}}

        return JSONResponse(list(result_list))


def get_candidate_sns_list():
    api = twitter.Api(access_token_key='833848464979079168-qhskxnXzEstVFlOtD6RDyA47OJetk4H',
                      access_token_secret='rJQaE6OrI6pFjcpXC7Aheq9ebslHyRVlVuLmt5FRWvVYv',
                      consumer_key='MHJ7LJmm1nGHLlNrN7lntMSB8',
                      consumer_secret='lxpIYyImUVVyIQfDyrEPi5HIh71CZLrnNBF2uRPfuNrmVUqICM')

    schedules = []
    candidate_color_dict = {'문재인': '#1870B9', '안희정': '#1870B9', '이재명': '#1870B9', '홍준표': '#c9151e', '김진태': '#c9151e',
                            '안철수': '#036241', '손학규': '#036241', '유승민': '#01B1EC', '심상정': '#FFCA08'}

    for candidate in get_candidates():
        if candidate.twitter is None:
            continue
        statuses = api.GetUserTimeline(screen_name=candidate.twitter)

        for status in statuses:
            created = datetime.strptime(status.created_at, '%a %b %d %H:%M:%S %z %Y').astimezone(pytz.timezone('Asia/Seoul'))
            contents_split = status.text.split('https')
            contents = ''
            for string in contents_split:
                contents += string.replace('&lt;', '').replace('&gt;', '')

            if '일정' in contents:
                contents += '\n'
                # print(contents)

                date_format_1 = re.compile('\d+[.]\d+')  # 00.00
                date_format_2 = re.compile('\d+월\s*\d+일')  # 00월 00일
                hour_format_1 = re.compile('(\d+:\d+)\s*(.+?)\n')  # 00:00
                hour_format_2 = re.compile('\n(\D+?)\s*(\d+시\s?\d*분?)\s?(.+?)\n')  # (오전) 00시 00분

                month, day, hour, minute = created.month, created.day, 00, 00
                if contents.find('내일') > 0:
                    date = created + timedelta(days=1)
                    month, day = date.month, date.day
                elif date_format_1.search(contents) is not None:
                    date = date_format_1.search(contents).group().split('.')
                    month, day = int(date[0]), int(date[1])
                elif date_format_2.search(contents) is not None:
                    date = date_format_2.search(contents).group().split('월')
                    month, day = int(date[0]), int(date[1].replace('일', '').strip())

                if hour_format_1.findall(contents) is not None:
                    for time in hour_format_1.finditer(contents):
                        schedule_time = time.group(1).split(':')
                        hour, minute = int(schedule_time[0]), int(schedule_time[1])
                        title = time.group(time.lastindex)
                        if status.user.name == '문재인':
                            if re.compile('일정]\s(.+?)\n').search(contents) is not None:
                                title = re.compile('일정]\s(.+?)\n').search(contents).group(1)

                        if title.find('…') > 0:
                            continue

                        if hour > 23:
                            hour -= 24
                            date = datetime(2017, month, day, hour, minute)
                            date += timedelta(days=1)
                        else:
                            date = datetime(2017, month, day, hour, minute)

                        schedules.append({'start': date.strftime('%Y-%m-%d %H:%M'),
                                          'title': status.user.name + ', ' + title, 'color': candidate_color_dict[status.user.name]})

                if hour_format_2.findall(contents) is not None:
                    for time in hour_format_2.finditer(contents):
                        schedule_time = time.group(time.lastindex-1).split('시')
                        hour = int(schedule_time[0])
                        if time.group(time.lastindex-1).find('분') > 0:
                            minute = int(schedule_time[1].replace('분', ''))

                        if time.lastindex == 3:
                            if any(word in time.group(time.lastindex-2) for word in ['오후', '저녁', '밤']):
                                hour += 12

                        title = time.group(time.lastindex).replace('에는', '')
                        if title.find('…') > 0:
                            continue

                        if hour > 23:
                            hour -= 24
                            date = datetime(2017, month, day, hour, minute)
                            date += timedelta(days=1)
                        else:
                            date = datetime(2017, month, day, hour, minute)

                        schedules.append({'start': date.strftime('%Y-%m-%d %H:%M'),
                                          'title': status.user.name + ', ' + title, 'color': candidate_color_dict[status.user.name]})

                continue

    schedules = sorted(schedules, key=lambda k: k['start'])
    return schedules


@cache_page(60 * 10)
def get_candidate_sns_api(request):
    if request.method == 'GET':
        result_list = get_candidate_sns_list()
        calendars = Calendar.objects.all()
        for calendar in calendars:
            if calendar.end is not None:
                result_list.append({'title': calendar.title, 'color': '#d3d3d3',
                                    'start': calendar.start.strftime('%Y-%m-%d %H:%M'),
                                    'end': calendar.end.strftime('%Y-%m-%d %H:%M')})
            else:
                result_list.append({'title': calendar.title, 'color': '#d3d3d3',
                                    'start': calendar.start.strftime('%Y-%m-%d %H:%M')})
        return JSONResponse(result_list)
    else:
        return Http404


def get_issue_keyword_list(date):
    if date is None:
        issue_keywords = IssueKeyword.objects.all().order_by('-date')
    else:
        issue_keywords = IssueKeyword.objects.filter(date=date)

    results = []
    temps = []
    temp_date = None
    for idx, issue in enumerate(issue_keywords):
        if idx == 0:
            temp_date = issue.date

        keywords = eval(issue.keywords)
        if len(keywords) != 0:
            issue_dict = {'candidate': issue.candidate, 'keywords': keywords}

            if temp_date == issue.date:
                temps.append(issue_dict)
            else:
                temps = sorted(temps, key=itemgetter('candidate'))
                results.append({'items': temps, 'date': temp_date})
                temp_date = issue.date
                temps = []

    if len(temps) != 0:
        temps = sorted(temps, key=itemgetter('candidate'))
        results.append({'items': temps, 'date': temp_date})

    return results


@cache_page(60 * 10)
def get_issue_keyword_api(request):
    if request.method == 'GET':
        return JSONResponse(get_issue_keyword_list(request.GET.get('date', None)))
    else:
        return Http404


def get_cheering_message_list(page):
    messages = CheeringMessage.objects.all().values('candidate', 'message', 'ip', 'created').order_by('-created')[page * 10:page * 10 + 10]
    return list(messages)


def create_cheering_message(request):
    body = JSONParser().parse(request)
    candidate = body.get('candidate', None)
    message = body.get('message', None)
    ip = body.get('ip', None)

    if candidate is not None and message is not None and ip is not None:
        new_message = CheeringMessage(candidate=candidate, message=message, ip=ip)
        new_message.save()
        return True

    return False


def cheering_message_api(request):
    if request.method == 'GET':
        page = request.GET.get('page', None)
        if page is None:
            page = 0
        return JSONResponse(get_cheering_message_list(page=page))

    elif request.method == 'POST':
        if create_cheering_message(request):
            return JSONResponse({'message': 'success'})
        else:
            return JSONResponse({'message': 'failure'})


def constellation_post(request):
    body = JSONParser().parse(request)
    request_constellation = body.get('constellation', None)

    if constellation is not None:
        result = constellation.constellation_chemistry(request_constellation, get_candidates())
        result = sorted(result, key=itemgetter('score'), reverse=True)

        max_obj = max(result, key=itemgetter('score'))
        result_dict = {'constellation': request_constellation, 'bests': [], 'rests': []}

        for obj in result:
            if obj['score'] == max_obj['score']:
                result_dict['bests'].append(obj)
                save_lucky_rating(obj['candidate'], 'star', request_constellation, None)
            else:
                result_dict['rests'].append(obj)

        return result_dict
    else:
        return None


@csrf_exempt
def constellation_api(request):
    if request.method == 'POST':
        result = constellation_post(request)
        return JSONResponse(result)
    else:
        return Http404


def blood_type_chemistry(request):
    body = JSONParser().parse(request)
    blood = body.get('blood', None)
    result_list = []
    for candidate in get_candidates():
        if candidate.blood_type is None or candidate.blood_type == '':
            continue
        score = blood_type.blood_chemistry(blood, candidate.blood_type)
        result_list.append({'candidate': candidate.candidate, 'blood': candidate.blood_type, 'score': score})

    result = sorted(result_list, key=itemgetter('score'), reverse=True)

    max_obj = max(result, key=itemgetter('score'))
    result_dict = {'bests': [], 'rests': []}

    for obj in result:
        if obj['score'] == max_obj['score']:
            result_dict['bests'].append(obj)
            save_lucky_rating(obj['candidate'], 'blood', blood, None)
        else:
            result_dict['rests'].append(obj)

    return result_dict


def zodiac_chemistry(request):
    body = JSONParser().parse(request)
    request_zodiac = body.get('zodiac', None)
    result_list = []
    for candidate in get_candidates():
        if candidate.zodiac is None or candidate.zodiac == '':
            continue
        score = zodiac.chemistry(request_zodiac, candidate.zodiac)
        result_list.append({'candidate': candidate.candidate, 'zodiac': candidate.zodiac, 'score': score})

    result = sorted(result_list, key=itemgetter('score'), reverse=True)

    max_obj = max(result, key=itemgetter('score'))
    result_dict = {'bests': [], 'rests': []}

    for obj in result:
        if obj['score'] == max_obj['score']:
            result_dict['bests'].append(obj)
            save_lucky_rating(obj['candidate'], 'zodiac', request_zodiac, None)
        else:
            result_dict['rests'].append(obj)

    return result_dict


def total_chemistry(request):
    body = JSONParser().parse(request)
    request_zodiac = body.get('zodiac', None)
    request_blood = body.get('blood', None)
    request_constellation = body.get('constellation', None)
    request_name = body.get('name', None)

    if request_zodiac is None or request_blood is None or request_constellation is None or request_name is None:
        return

    result_list = []
    for candidate in get_candidates():
        score_to, score_to_list, name_to_list = hangle.name_chemistry(request_name, candidate.candidate)
        score_from, score_from_list, name_from_list = hangle.name_chemistry(candidate.candidate, request_name)
        name_score = score_from + score_to

        if candidate.blood_type != '':
            blood_score = blood_type.blood_chemistry(request_blood, candidate.blood_type)
        else:
            blood_score = 0

        constellation_score = constellation.constellation_chemistry_one(request_constellation, candidate.constellation)
        zodiac_score = zodiac.chemistry(request_zodiac, candidate.zodiac)

        total_score = name_score + blood_score + constellation_score + zodiac_score
        total_score = total_score / 5

        result_list.append({'candidate': candidate.candidate, 'name': name_score, 'blood': blood_score, 'constellation': constellation_score, 'zodiac': zodiac_score, 'score': total_score})

    result = sorted(result_list, key=itemgetter('score'), reverse=True)

    save_string = request_zodiac + '_' + request_blood + '_' + request_constellation + '_' + request_name
    save_lucky_rating(result[0]['candidate'], 'total', save_string, result[0]['score'])

    rank = LuckyRating.objects.filter(type='total', score__gt=result[0]['score']).count() + 1
    result[0]['rank'] = rank

    return result



@csrf_exempt
def blood_type_chemistry_api(request):
    if request.method == 'POST':
        result = blood_type_chemistry(request)
        return JSONResponse(result)
    else:
        return Http404


def save_lucky_result(request):
    body = JSONParser().parse(request)
    lucky_type = body.get('type', None)
    candidate = body.get('candidate', None)
    count = body.get('count', None)
    save_lucky_rating(candidate, lucky_type, count, None)

    return {'type': lucky_type, 'candidate': candidate, 'count': count}


@csrf_exempt
def save_lucky_result_api(request):
    if request.method == 'POST':
        save_lucky_result(request)
        return HttpResponse(status=200)
    else:
        return Http404


@csrf_exempt
def upload(request):
    if request.method == 'POST':
        body = JSONParser().parse(request)
        file_format, imgstr = str(body.get('image')).split(';base64,')
        ext = file_format.split('/')[-1]
        today_string = datetime.now().strftime('%Y%m%d_%H%M%S_')

        if os.getenv('GAE_INSTANCE'):
            gcs = storage.Client()
            bucket = gcs.get_bucket('daesun2017.appspot.com')
            filename = 'share/' + today_string + str(random.random()).split('.')[1] + "." + ext
            blob = bucket.blob(filename)
            blob.upload_from_string(base64.b64decode(imgstr), content_type=file_format)

            return HttpResponse(blob.public_url)
        else:
            file_name = "image/" + today_string + str(random.random()) + "." + ext
            f = open(settings.MEDIA_ROOT + file_name, "wb")
            f.write(base64.b64decode(imgstr))
            f.close()
            return HttpResponse(settings.MEDIA_URL + file_name)
