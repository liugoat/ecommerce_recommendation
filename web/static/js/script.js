// 电商推荐平台JavaScript脚本

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 为商品卡片添加点击事件
    const productCards = document.querySelectorAll('.product-card');
    productCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // 避免在点击按钮或链接时重复触发卡片的点击事件
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                return;
            }
            
            // 获取商品ID并记录点击行为
            const productId = this.dataset.productId;
            if (productId) {
                recordClick(productId);
            }
            
            // 获取商品链接并跳转
            const link = this.querySelector('a');
            if (link) {
                window.location.href = link.href;
            }
        });
    });
    
    // 添加商品卡片悬停效果
    const cards = document.querySelectorAll('.product-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.cursor = 'pointer';
        });
    });
    
    // 搜索功能
    const searchInput = document.querySelector('.search-box');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
    
    // 添加加载动画
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.style.cssText = `
        display: none;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 20px;
        border-radius: 10px;
        z-index: 9999;
    `;
    loadingIndicator.innerHTML = '<i class="fas fa-spinner fa-spin fa-2x"></i> <span class="ms-2">加载中...</span>';
    document.body.appendChild(loadingIndicator);
    
    // 显示加载指示器
    window.showLoading = function() {
        loadingIndicator.style.display = 'block';
    };
    
    // 隐藏加载指示器
    window.hideLoading = function() {
        loadingIndicator.style.display = 'none';
    };
});

// 格式化货币函数
function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2);
}

// 限制文本长度函数
function truncateText(text, maxLength) {
    if (text.length <= maxLength) {
        return text;
    }
    return text.substr(0, maxLength) + '...';
}

// 搜索功能
function performSearch() {
    const searchTerm = document.querySelector('.search-box').value.toLowerCase();
    if (!searchTerm) return;
    
    showLoading();
    
    // 这里可以实现实际的搜索逻辑
    // 暂时只是模拟搜索行为
    setTimeout(() => {
        hideLoading();
        alert(`搜索 "${searchTerm}" 的功能将在后续版本中实现`);
    }, 1000);
}

// 添加平滑滚动效果
function smoothScrollTo(target) {
    const element = document.querySelector(target);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth'
        });
    }
}

// 记录用户点击商品的行为
function recordClick(productId) {
    // 检查用户是否已登录
    if (typeof session !== 'undefined' && session.user_id) {
        fetch(`/api/record_click/${productId}`)
            .then(response => response.json())
            .then(data => {
                if(data.status === 'success') {
                    console.log('点击记录已保存');
                } else if(data.status === 'not logged in') {
                    console.log('用户未登录，无法记录行为');
                }
            })
            .catch(error => console.error('记录点击时出错:', error));
    }
}

// 收藏相关操作
function toggleFavorite(productId, buttonElem) {
    // 判断当前是收藏还是取消
    const action = buttonElem.dataset.favorited === '1' ? 'DELETE' : 'POST';
    fetch('/api/favorites', {
        method: action,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId })
    }).then(r => r.json())
      .then(resp => {
          if (resp.status === 'ok') {
              if (action === 'POST') {
                  buttonElem.dataset.favorited = '1';
                  buttonElem.innerText = '已收藏';
              } else {
                  buttonElem.dataset.favorited = '0';
                  buttonElem.innerText = '收藏';
              }
          } else if (resp.error) {
              alert(resp.error);
          }
      })
      .catch(err => {
          console.error('收藏错误', err);
          // 网络或fetch不支持，回退到表单提交
          try {
              const form = document.createElement('form');
              form.method = 'POST';
              form.action = '/favorites/form_toggle';
              const pidInput = document.createElement('input');
              pidInput.type = 'hidden';
              pidInput.name = 'product_id';
              pidInput.value = productId;
              const actionInput = document.createElement('input');
              actionInput.type = 'hidden';
              actionInput.name = 'action';
              actionInput.value = (action === 'POST') ? 'add' : 'remove';
              form.appendChild(pidInput);
              form.appendChild(actionInput);
              document.body.appendChild(form);
              form.submit();
          } catch (e) {
              alert('操作失败');
          }
      });
}

// 在商品卡片上添加收藏按钮（如果不存在）
function ensureFavoriteButtons() {
    document.querySelectorAll('.product-card').forEach(card => {
        if (card.querySelector('.fav-btn')) return;
        const pid = card.dataset.productId;
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm btn-outline-warning fav-btn';
        btn.style.marginTop = '8px';
        btn.dataset.favorited = '0';
        btn.innerText = '收藏';
        btn.onclick = function(e) {
            e.stopPropagation();
            toggleFavorite(pid, btn);
        };
        const container = card.querySelector('.mt-3') || card.querySelector('.card-body');
        if (container) container.appendChild(btn);
    });
}

document.addEventListener('DOMContentLoaded', function() { ensureFavoriteButtons(); });