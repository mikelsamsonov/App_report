import pandas as pd
import telegram
import matplotlib.pyplot as plt
import seaborn as sns
import pandahouse
import io
from read_db.CH import Getch
import os

sns.set()


def get_plot(data):
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    fig.suptitle('Статистика по ЛЕНТЕ за предыдущие 7 дней')

    plot_dict = {(0, 0): {'y': 'DAU', 'title': 'Уникальные пользователи'},
                 (0, 1): {'y': 'likes', 'title': 'Likes'},
                 (1, 0): {'y': 'views', 'title': 'Views'},
                 (1, 1): {'y': 'CTR', 'title': 'CTR'}}

    for i in range(2):
        for j in range(2):
            sns.lineplot(ax=axes[i, j], data=data, x='date', y=plot_dict[(i, j)]['y'])
            axes[i, j].set_title(plot_dict[(i, j)]['title'])
            axes[i, j].set(xlabel=None)
            axes[i, j].set(ylabel=None)
            for ind, label in enumerate(axes[i, j].get_xticklabels()):
                if ind % 3 == 0:
                    label.set_visible(True)
                else:
                    label.set_visible(False)

    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.name = 'feed_statistics.png'
    plot_object.seek(0)
    plt.close()
    return plot_object


def feed_report(chat=None):
    chat_id = chat or 904623834
    bot = telegram.Bot(token=os.environ.get('REPORT_BOT_TOKEN'))
    msg = '''Отчет по ленте за {date}
Events: {events}    
DAU: {users} ({to_users_day_ago:+.2%} к дню назад,  {to_users_week_ago:+.2%} к неделе назад)
Likes: {likes} ({to_likes_day_ago:+.2%} к дню назад,  {to_likes_week_ago:+.2%} к неделе назад)
Views: {views} ({to_views_day_ago:+.2%} к дню назад,  {to_views_week_ago:+.2%} к неделе назад)
CTR: {ctr:.2f}% ({to_ctr_day_ago:+.2%} к дню назад,  {to_ctr_week_ago:+.2%} к неделе назад)
Posts: {posts} ({to_posts_day_ago:+.2%} к дню назад,  {to_posts_week_ago:+.2%} к неделе назад)
Likes per user: {lpu:.2f} ({to_lpu_day_ago:+.2%} к дню назад,  {to_lpu_week_ago:+.2%} к неделе назад)
    '''
    data = Getch('''SELECT
                          toDate(time) as date,
                          uniqExact(user_id) as DAU,
                          countIf(user_id, action='view') as views,
                          countIf(user_id, action='like') as likes,
                          100 * likes / views as CTR,
                          views + likes as events,
                          uniqExact(post_id) as posts,
                          likes / DAU as LPU
                    FROM simulator.feed_actions
                    WHERE toDate(time) between  today() - 8 and today() - 1
                    GROUP BY date
                    ORDER BY date''').df

    today = pd.Timestamp('now') - pd.DateOffset(days=1)  # ближайший полный день, т.е. вчерашний 
    day_ago = today - pd.DateOffset(days=1)
    week_ago = today - pd.DateOffset(days=7)

    data['date'] = pd.to_datetime(data['date']).dt.date
    data = data.astype({'DAU': int, 'views': int, 'likes': int, 'events': int, 'posts': int})  
    # меняем тип данных на int, чтобы были как положительные так и отрицательные значения изменения
    report = msg.format(date=today.date(),
                        events=data[data['date'] == today.date()]['events'].iloc[0],
                        users=data[data['date'] == today.date()]['DAU'].iloc[0],
                        # (текущий день - предыдущий день) / предыдущий день
                        to_users_day_ago=(data[data['date'] == today.date()]['DAU'].iloc[0]
                                          - data[data['date'] == day_ago.date()]['DAU'].iloc[0])
                                         / data[data['date'] == day_ago.date()]['DAU'].iloc[0],
                        to_users_week_ago=(data[data['date'] == today.date()]['DAU'].iloc[0]
                                          - data[data['date'] == week_ago.date()]['DAU'].iloc[0])
                                         / data[data['date'] == week_ago.date()]['DAU'].iloc[0],

                        likes=data[data['date'] == today.date()]['likes'].iloc[0],
                        to_likes_day_ago=(data[data['date'] == today.date()]['likes'].iloc[0]
                                          - data[data['date'] == day_ago.date()]['likes'].iloc[0])
                                         / data[data['date'] == day_ago.date()]['likes'].iloc[0],
                        to_likes_week_ago=(data[data['date'] == today.date()]['likes'].iloc[0]
                                          - data[data['date'] == week_ago.date()]['likes'].iloc[0])
                                         / data[data['date'] == week_ago.date()]['likes'].iloc[0],

                        views=data[data['date'] == today.date()]['views'].iloc[0],
                        to_views_day_ago=(data[data['date'] == today.date()]['views'].iloc[0]
                                          - data[data['date'] == day_ago.date()]['views'].iloc[0])
                                         / data[data['date'] == day_ago.date()]['views'].iloc[0],
                        to_views_week_ago=(data[data['date'] == today.date()]['views'].iloc[0]
                                          - data[data['date'] == week_ago.date()]['views'].iloc[0])
                                         / data[data['date'] == week_ago.date()]['views'].iloc[0],

                        ctr=data[data['date'] == today.date()]['CTR'].iloc[0],
                        to_ctr_day_ago=(data[data['date'] == today.date()]['CTR'].iloc[0]
                                          - data[data['date'] == day_ago.date()]['CTR'].iloc[0])
                                         / data[data['date'] == day_ago.date()]['CTR'].iloc[0],
                        to_ctr_week_ago=(data[data['date'] == today.date()]['CTR'].iloc[0]
                                          - data[data['date'] == week_ago.date()]['CTR'].iloc[0])
                                         / data[data['date'] == week_ago.date()]['CTR'].iloc[0],

                        posts=data[data['date'] == today.date()]['posts'].iloc[0],
                        to_posts_day_ago=(data[data['date'] == today.date()]['posts'].iloc[0]
                                          - data[data['date'] == day_ago.date()]['posts'].iloc[0])
                                         / data[data['date'] == day_ago.date()]['posts'].iloc[0],
                        to_posts_week_ago=(data[data['date'] == today.date()]['posts'].iloc[0]
                                          - data[data['date'] == week_ago.date()]['posts'].iloc[0])
                                         / data[data['date'] == week_ago.date()]['posts'].iloc[0],

                        lpu=data[data['date'] == today.date()]['LPU'].iloc[0],
                        to_lpu_day_ago=(data[data['date'] == today.date()]['LPU'].iloc[0]
                                          - data[data['date'] == day_ago.date()]['LPU'].iloc[0])
                                         / data[data['date'] == day_ago.date()]['LPU'].iloc[0],
                        to_lpu_week_ago=(data[data['date'] == today.date()]['LPU'].iloc[0]
                                          - data[data['date'] == week_ago.date()]['LPU'].iloc[0])
                                         / data[data['date'] == week_ago.date()]['LPU'].iloc[0]
                        )

    plot_object = get_plot(data)
    bot.sendMessage(chat_id=chat_id, text=report)
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)


try:
    feed_report(chat=None)
except Exception as e:
    print(e)
