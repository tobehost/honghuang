// primordial-culture-site-311714/frontend/public/static/js/main.js

(function() {
  'use strict';

  // 全局状态管理
  const AppState = {
    currentUser: null,
    token: null,
    currentCategory: 'all',
    contents: [],
    orders: []
  };

  // API 基础路径
  const API_BASE = '/api';

  // 工具函数：显示提示消息
  function showToast(message, type = 'info') {
    const toast = $('<div>')
      .addClass(`alert alert-${type} alert-dismissible fade show`)
      .css({
        position: 'fixed',
        top: '80px',
        right: '20px',
        zIndex: 9999,
        minWidth: '300px'
      })
      .html(`
        ${message}
        <button type="button" class="close" data-dismiss="alert">
          <span>&times;</span>
        </button>
      `);
    
    $('body').append(toast);
    setTimeout(() => toast.alert('close'), 3000);
  }

  // 工具函数：发起 API 请求（增强错误处理）
  function apiRequest(endpoint, options = {}) {
    const config = {
      url: `${API_BASE}${endpoint}`,
      method: options.method || 'GET',
      contentType: 'application/json',
      dataType: 'json',
      timeout: 15000,
      ...options
    };

    if (AppState.token) {
      config.headers = {
        'Authorization': `Bearer ${AppState.token}`
      };
    }

    if (options.data && config.method !== 'GET') {
      config.data = JSON.stringify(options.data);
    }

    return $.ajax(config)
      .fail(function(jqXHR, textStatus, errorThrown) {
        if (jqXHR.status === 401) {
          handleLogout();
          showToast('登录已过期，请重新登录', 'warning');
        } else if (jqXHR.status === 403) {
          showToast('权限不足，无法访问', 'danger');
        } else if (jqXHR.status === 404) {
          showToast('请求的资源不存在', 'warning');
        } else if (jqXHR.status === 500) {
          showToast('服务器错误，请稍后重试', 'danger');
        } else if (textStatus === 'timeout') {
          showToast('请求超时，请检查网络连接', 'warning');
        } else {
          showToast('请求失败，请稍后重试', 'danger');
        }
      });
  }

  // 初始化登录状态
  function initAuthState() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
      try {
        AppState.token = token;
        AppState.currentUser = JSON.parse(user);
        updateAuthUI();
      } catch (e) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
  }

  // 更新认证相关UI
  function updateAuthUI() {
    if (AppState.currentUser) {
      $('#loginBtn').hide();
      $('#registerBtn').hide();
      $('#userDropdown').show();
      $('#usernameDisplay').text(AppState.currentUser.username);
      
      const levelText = AppState.currentUser.membership_level === 'vip' ? 'VIP会员' : '普通会员';
      $('#membershipLevel').text(levelText);
    } else {
      $('#loginBtn').show();
      $('#registerBtn').show();
      $('#userDropdown').hide();
    }
  }

  // 用户注册
  function handleRegister() {
    const username = $('#registerUsername').val().trim();
    const password = $('#registerPassword').val();
    const confirmPassword = $('#registerConfirmPassword').val();

    if (!username || !password) {
      showToast('请填写完整信息', 'warning');
      return;
    }

    if (password !== confirmPassword) {
      showToast('两次密码输入不一致', 'warning');
      return;
    }

    apiRequest('/user/register', {
      method: 'POST',
      data: { username, password }
    })
      .done(function(response) {
        if (response.success) {
          showToast('注册成功，请登录', 'success');
          $('#registerModal').modal('hide');
          $('#registerForm')[0].reset();
          setTimeout(() => $('#loginModal').modal('show'), 500);
        } else {
          showToast(response.message || '注册失败', 'danger');
        }
      });
  }

  // 用户登录
  function handleLogin() {
    const username = $('#loginUsername').val().trim();
    const password = $('#loginPassword').val();

    if (!username || !password) {
      showToast('请填写用户名和密码', 'warning');
      return;
    }

    apiRequest('/user/login', {
      method: 'POST',
      data: { username, password }
    })
      .done(function(response) {
        if (response.success) {
          AppState.token = response.token;
          AppState.currentUser = response.user;
          
          localStorage.setItem('token', response.token);
          localStorage.setItem('user', JSON.stringify(response.user));
          
          showToast('登录成功', 'success');
          $('#loginModal').modal('hide');
          $('#loginForm')[0].reset();
          updateAuthUI();
        } else {
          showToast(response.message || '登录失败', 'danger');
        }
      });
  }

  // 用户退出登录
  function handleLogout() {
    AppState.token = null;
    AppState.currentUser = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    showToast('已退出登录', 'info');
    updateAuthUI();
    
    if ($('#userPanel').is(':visible')) {
      loadContents('all');
      $('#contentSection').show();
      $('#userPanel').hide();
    }
  }

  // 加载内容列表
  function loadContents(category = 'all') {
    AppState.currentCategory = category;
    
    $('#contentGrid').html('<div class="loading">正在加载内容</div>');
    
    const endpoint = category === 'all' ? '/content' : `/content?type=${category}`;
    
    apiRequest(endpoint)
      .done(function(response) {
        if (response.success && response.data) {
          AppState.contents = response.data;
          renderContents(response.data);
        } else {
          $('#contentGrid').html('<div class="text-center text-muted py-5">暂无内容</div>');
        }
      })
      .fail(function() {
        $('#contentGrid').html('<div class="text-center text-danger py-5">加载失败，请刷新重试</div>');
      });
  }

  // 渲染内容列表
  function renderContents(contents) {
    if (!contents || contents.length === 0) {
      $('#contentGrid').html('<div class="text-center text-muted py-5">暂无内容</div>');
      return;
    }

    const typeMap = {
      novel: '小说',
      music: '音乐',
      anime: '动漫',
      wallpaper: '壁纸'
    };
    
    const contentHTML = contents.map(item => `
      <div class="col-md-4 col-lg-3">
        <div class="content-card" data-id="${item.id}">
          <img src="${item.image_url || 'https://via.placeholder.com/300x250'}" alt="${item.title}">
          <div class="card-body">
            <span class="badge badge-warning mb-2">${typeMap[item.type] || item.type}</span>
            <h5 class="card-title">${item.title}</h5>
            <p class="card-text">${item.description || '暂无描述'}</p>
            <div class="d-flex justify-content-between align-items-center mt-3">
              <span class="price">¥${item.price}</span>
              <button class="btn btn-primary btn-sm buy-btn" data-id="${item.id}">
                立即购买
              </button>
            </div>
          </div>
        </div>
      </div>
    `).join('');

    $('#contentGrid').html(contentHTML);
  }

  // 处理购买功能
  function handlePurchase(contentId) {
    if (!AppState.currentUser) {
      showToast('请先登录', 'warning');
      $('#loginModal').modal('show');
      return;
    }

    const content = AppState.contents.find(c => c.id === contentId);
    if (!content) {
      showToast('内容不存在', 'danger');
      return;
    }

    if (confirm(`确认购买《${content.title}》？价格：¥${content.price}`)) {
      apiRequest('/order', {
        method: 'POST',
        data: { content_id: contentId }
      })
        .done(function(response) {
          if (response.success) {
            showToast('订单创建成功', 'success');
            
            if (confirm('是否立即支付？')) {
              handlePayment(response.data.id);
            }
          } else {
            showToast(response.message || '购买失败', 'danger');
          }
        });
    }
  }

  // 处理支付功能
  function handlePayment(orderId) {
    apiRequest(`/order/${orderId}/pay`, {
      method: 'POST'
    })
      .done(function(response) {
        if (response.success) {
          showToast('支付成功', 'success');
        } else {
          showToast(response.message || '支付失败', 'danger');
        }
      });
  }

  // 加载用户订单
  function loadUserOrders() {
    if (!AppState.currentUser) {
      return;
    }

    $('#orderList').html('<div class="loading">正在加载订单</div>');

    apiRequest('/order')
      .done(function(response) {
        if (response.success && response.data) {
          AppState.orders = response.data;
          renderOrders(response.data);
        } else {
          $('#orderList').html('<div class="text-center text-muted py-5">暂无订单</div>');
        }
      })
      .fail(function() {
        $('#orderList').html('<div class="text-center text-danger py-5">加载失败</div>');
      });
  }

  // 渲染订单列表
  function renderOrders(orders) {
    if (!orders || orders.length === 0) {
      $('#orderList').html('<div class="text-center text-muted py-5">暂无订单</div>');
      return;
    }

    const statusMap = {
      pending: '待支付',
      paid: '已支付',
      cancelled: '已取消',
      refunded: '已退款'
    };

    const ordersHTML = orders.map(order => {
      const statusClass = order.payment_status === 'paid' ? 'paid' : 'pending';
      const content = order.content || {};
      
      return `
        <div class="order-item">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0">订单号: ${order.id}</h6>
            <span class="status ${statusClass}">${statusMap[order.payment_status] || order.payment_status}</span>
          </div>
          <p class="mb-1"><strong>商品:</strong> ${content.title || '未知商品'}</p>
          <p class="mb-1"><strong>价格:</strong> ¥${content.price || 0}</p>
          <p class="mb-1"><strong>时间:</strong> ${new Date(order.payment_time).toLocaleString('zh-CN')}</p>
          ${order.payment_status === 'pending' ? `
            <button class="btn btn-primary btn-sm mt-2 pay-order-btn" data-id="${order.id}">
              立即支付
            </button>
          ` : ''}
        </div>
      `;
    }).join('');

    $('#orderList').html(ordersHTML);
  }

  // 显示会员中心
  function showUserPanel() {
    if (!AppState.currentUser) {
      showToast('请先登录', 'warning');
      $('#loginModal').modal('show');
      return;
    }

    $('#contentSection').hide();
    $('#userPanel').show();
    
    $('#userPanelUsername').text(AppState.currentUser.username);
    const levelText = AppState.currentUser.membership_level === 'vip' ? 'VIP会员' : '普通会员';
    $('#userPanelMembership').text(levelText);
    
    loadUserOrders();
  }

  // 返回首页
  function showHomePage() {
    $('#userPanel').hide();
    $('#contentSection').show();
    loadContents(AppState.currentCategory);
  }

  // 初始化轮播图
  function initCarousel() {
    $('.carousel').carousel({
      interval: 5000,
      pause: 'hover'
    });
  }

  // 事件绑定
  function bindEvents() {
    $('#registerBtn, #showRegisterLink').on('click', function(e) {
      e.preventDefault();
      $('#loginModal').modal('hide');
      $('#registerModal').modal('show');
    });

    $('#loginBtn, #showLoginLink').on('click', function(e) {
      e.preventDefault();
      $('#registerModal').modal('hide');
      $('#loginModal').modal('show');
    });

    $('#registerForm').on('submit', function(e) {
      e.preventDefault();
      handleRegister();
    });

    $('#loginForm').on('submit', function(e) {
      e.preventDefault();
      handleLogin();
    });

    $('#logoutBtn').on('click', function(e) {
      e.preventDefault();
      handleLogout();
    });

    $('#userCenterBtn').on('click', function(e) {
      e.preventDefault();
      showUserPanel();
    });

    $('#backToHomeBtn').on('click', function(e) {
      e.preventDefault();
      showHomePage();
    });

    $('.category-nav .nav-link').on('click', function(e) {
      e.preventDefault();
      const category = $(this).data('category');
      $('.category-nav .nav-link').removeClass('active');
      $(this).addClass('active');
      loadContents(category);
    });

    $(document).on('click', '.buy-btn', function() {
      const contentId = parseInt($(this).data('id'));
      handlePurchase(contentId);
    });

    $(document).on('click', '.pay-order-btn', function() {
      const orderId = parseInt($(this).data('id'));
      handlePayment(orderId);
    });
  }

  // 页面加载完成后初始化
  $(document).ready(function() {
    initAuthState();
    initCarousel();
    bindEvents();
    loadContents('all');
  });

})();