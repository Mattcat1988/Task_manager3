
        document.addEventListener('DOMContentLoaded', function() {
            var calendarEl = document.getElementById('calendar');

            var calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'dayGridMonth',
                events: [
                    {% for task in tasks %}
                    {% if task['due_date'] %}
                    {
                        title: "#{{ task['task_number'] }} - {{ task['title'] }}{% if task['assignee_name'] %} - {{ task['assignee_name'] }}{% endif %}",
                        start: "{{ task['due_date'] }}",
                        url: "/task/{{ task['id'] }}"
                    },
                    {% endif %}
                    {% endfor %}
                ],
                eventClick: function(info) {
                    info.jsEvent.preventDefault();
                    if (info.event.url) {
                        window.location.href = info.event.url;  // Переход по ссылке на задачу
                    }
                }
            });

            calendar.render();
        });
