document.addEventListener('DOMContentLoaded', function () {
    var translations = window.QAMQOR_DOM_TRANSLATIONS || {};

    function translateDom() {
        if (!translations || Object.keys(translations).length === 0) return;

        function normalizeText(value) {
            return (value || '').replace(/\s+/g, ' ').trim();
        }

        var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
        var node;
        while ((node = walker.nextNode())) {
            var parent = node.parentElement;
            if (!parent || ['SCRIPT', 'STYLE', 'NOSCRIPT'].indexOf(parent.tagName) !== -1) continue;
            var text = normalizeText(node.nodeValue);
            if (!text || !translations[text]) continue;
            node.nodeValue = translations[text];
        }

        document.querySelectorAll('[placeholder], [title], [aria-label], input[type="button"], input[type="submit"], button').forEach(function (el) {
            ['placeholder', 'title', 'aria-label', 'value'].forEach(function (attr) {
                var current = el.getAttribute(attr);
                var normalized = normalizeText(current);
                if (normalized && translations[normalized]) {
                    el.setAttribute(attr, translations[normalized]);
                }
            });
        });

        var titleKey = normalizeText(document.title);
        if (titleKey && translations[titleKey]) {
            document.title = translations[titleKey];
        }
    }

    translateDom();

    const notificationBadge = document.getElementById('notificationCount');
    const notificationList = document.getElementById('notificationList');
    const markAllReadBtn = document.getElementById('markAllRead');

    function fetchNotificationCount() {
        fetch('/api/notifications/count')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                var count = data.count || 0;
                if (notificationBadge) {
                    notificationBadge.textContent = count;
                    if (count > 0) {
                        notificationBadge.classList.remove('d-none');
                    } else {
                        notificationBadge.classList.add('d-none');
                    }
                }
            })
            .catch(function () { /* silent */ });
    }

    if (notificationBadge || notificationList || markAllReadBtn) {
        fetchNotificationCount();
        setInterval(fetchNotificationCount, 30000);
    }

    var notifDropdownEl = document.getElementById('notificationsDropdown');
    if (notifDropdownEl) {
        notifDropdownEl.addEventListener('show.bs.dropdown', function () {
            loadNotifications();
        });
    }

    function loadNotifications() {
        fetch('/api/notifications')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (!notificationList) return;
                var items = data.notifications || [];
                if (items.length === 0) {
                    notificationList.innerHTML =
                        '<div class="text-center py-4 text-muted">' +
                            '<i class="fas fa-bell-slash fa-2x mb-2 d-block"></i>' +
                            '<span class="small">' + (translations['Нет новых уведомлений'] || 'Нет новых уведомлений') + '</span>' +
                        '</div>';
                    return;
                }
                var TYPE_MAP = {
                    info:    { cls: 'info',    icon: 'fa-info-circle' },
                    success: { cls: 'message', icon: 'fa-check-circle' },
                    warning: { cls: 'alert',   icon: 'fa-exclamation-triangle' },
                    danger:  { cls: 'alert',   icon: 'fa-exclamation-circle' },
                };
                var html = '';
                items.forEach(function (n) {
                    var meta = TYPE_MAP[n.type] || TYPE_MAP.info;
                    html +=
                        '<div class="notification-item' + (n.read ? '' : ' unread') + '" ' +
                             'data-id="' + n.id + '" ' +
                             'data-link="' + (n.link ? escapeHtml(n.link) : '') + '">' +
                            '<div class="notif-icon ' + meta.cls + '">' +
                                '<i class="fas ' + meta.icon + '"></i>' +
                            '</div>' +
                            '<div class="notif-text">' +
                                '<p>' + escapeHtml(n.title || '') + '</p>' +
                                '<p class="text-muted small mb-0">' + escapeHtml(n.message) + '</p>' +
                                '<div class="notif-time">' + formatDateRu(n.created_at) + '</div>' +
                            '</div>' +
                        '</div>';
                });
                notificationList.innerHTML = html;

                notificationList.querySelectorAll('.notification-item').forEach(function (item) {
                    item.addEventListener('click', function () {
                        var id = this.getAttribute('data-id');
                        var link = this.getAttribute('data-link');
                        this.classList.remove('unread');
                        markNotificationRead(id);
                        if (link) {
                            window.location.href = link;
                        }
                    });
                });
            })
            .catch(function () { /* silent */ });
    }

    function markNotificationRead(id) {
        fetch('/api/notifications/' + id + '/read', { method: 'POST' })
            .then(function () { fetchNotificationCount(); })
            .catch(function () { /* silent */ });
    }

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function (e) {
            e.preventDefault();
            fetch('/api/notifications/read-all', { method: 'POST' })
                .then(function () {
                    fetchNotificationCount();
                    if (notificationList) {
                        notificationList.querySelectorAll('.notification-item.unread').forEach(function (el) {
                            el.classList.remove('unread');
                        });
                    }
                })
                .catch(function () { /* silent */ });
        });
    }

    var tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function (el) {
        new bootstrap.Tooltip(el);
    });

    var popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    popoverTriggerList.forEach(function (el) {
        new bootstrap.Popover(el);
    });

    var flashAlerts = document.querySelectorAll('.flash-alert');
    flashAlerts.forEach(function (alert) {
        setTimeout(function () {
            alert.classList.add('fade-out');
            setTimeout(function () {
                var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) bsAlert.close();
            }, 400);
        }, 5000);
    });

    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var href = this.getAttribute('href');
            if (!href || href === '#' || href.length < 2) return;
            if (this.hasAttribute('data-bs-toggle') || this.hasAttribute('data-bs-dismiss')) return;
            try {
                var target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            } catch (err) {
            }
        });
    });

    window.confirmDelete = function (message, title) {
        return new Promise(function (resolve) {
            var overlay = document.createElement('div');
            overlay.className = 'confirm-dialog-overlay';
            overlay.innerHTML =
                '<div class="confirm-dialog">' +
                    '<div class="confirm-icon"><i class="fas fa-trash-alt"></i></div>' +
                    '<h5 class="mb-2">' + escapeHtml(title || (translations['Удаление'] || 'Удаление')) + '</h5>' +
                    '<p class="text-muted mb-4">' + escapeHtml(message || (translations['Вы уверены? Это действие нельзя отменить.'] || 'Вы уверены? Это действие нельзя отменить.')) + '</p>' +
                    '<div class="d-flex justify-content-center gap-3">' +
                        '<button class="btn btn-secondary px-4 btn-cancel">' + (translations['Отмена'] || 'Отмена') + '</button>' +
                        '<button class="btn btn-danger px-4 btn-confirm">' + (translations['Удалить'] || 'Удалить') + '</button>' +
                    '</div>' +
                '</div>';

            document.body.appendChild(overlay);

            overlay.querySelector('.btn-cancel').addEventListener('click', function () {
                overlay.remove();
                resolve(false);
            });

            overlay.querySelector('.btn-confirm').addEventListener('click', function () {
                overlay.remove();
                resolve(true);
            });

            overlay.addEventListener('click', function (e) {
                if (e.target === overlay) {
                    overlay.remove();
                    resolve(false);
                }
            });
        });
    };

    document.querySelectorAll('[data-confirm-delete]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            e.preventDefault();
            var msg = this.getAttribute('data-confirm-delete') || 'Вы уверены? Это действие нельзя отменить.';
            var href = this.getAttribute('href') || this.getAttribute('data-href');
            confirmDelete(msg).then(function (ok) {
                if (ok && href) {
                    window.location.href = href;
                }
            });
        });
    });

    document.querySelectorAll('form[data-confirm-delete-form]').forEach(function (form) {
        var confirmed = false;
        form.addEventListener('submit', function (e) {
            if (confirmed) return;
            e.preventDefault();
            var msg = form.getAttribute('data-confirm-message') || 'Вы уверены? Это действие нельзя отменить.';
            confirmDelete(msg).then(function (ok) {
                if (ok) {
                    confirmed = true;
                    form.submit();
                }
            });
        });
    });

    var MONTHS_RU_SHORT = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
    var MONTHS_RU = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];

    window.formatDateRu = formatDateRu;

    function formatDateRu(dateStr) {
        if (!dateStr) return '';
        var d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        var day = d.getDate();
        var month = MONTHS_RU[d.getMonth()];
        var year = d.getFullYear();
        var hours = String(d.getHours()).padStart(2, '0');
        var mins = String(d.getMinutes()).padStart(2, '0');
        return day + ' ' + month + ' ' + year + ', ' + hours + ':' + mins;
    }

    window.formatDateShortRu = function (dateStr) {
        if (!dateStr) return '';
        var d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        return d.getDate() + ' ' + MONTHS_RU_SHORT[d.getMonth()];
    };

    document.querySelectorAll('[data-date]').forEach(function (el) {
        var raw = el.getAttribute('data-date');
        el.textContent = formatDateRu(raw);
    });

    document.querySelectorAll('.star-rating').forEach(function (widget) {
        var inputs = widget.querySelectorAll('input[type="radio"]');
        var labels = widget.querySelectorAll('label');

        labels.forEach(function (label) {
            label.addEventListener('click', function () {
                var value = this.getAttribute('for');
                var input = document.getElementById(value);
                if (input) {
                    input.checked = true;
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });

            label.addEventListener('mouseenter', function () {
                var targetValue = parseInt(this.getAttribute('data-value') || '0', 10);
                labels.forEach(function (l) {
                    var lv = parseInt(l.getAttribute('data-value') || '0', 10);
                    if (lv <= targetValue) {
                        l.style.color = '#fbbf24';
                    } else {
                        l.style.color = '#d1d5db';
                    }
                });
            });
        });

        widget.addEventListener('mouseleave', function () {
            var checkedInput = widget.querySelector('input:checked');
            var checkedVal = checkedInput ? parseInt(checkedInput.value, 10) : 0;
            labels.forEach(function (l) {
                var lv = parseInt(l.getAttribute('data-value') || '0', 10);
                if (lv <= checkedVal) {
                    l.style.color = '#fbbf24';
                } else {
                    l.style.color = '#d1d5db';
                }
            });
        });
    });

    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

});
