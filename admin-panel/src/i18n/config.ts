import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  en: {
    translation: {
      app: {
        title: 'Admin Panel'
      },
      nav: {
        dashboard: 'Dashboard',
        boxes: 'Boxes',
        cases: 'Cases',
        items: 'Items',
        users: 'Users',
        audit: 'Audit Logs',
        reports: 'Reports',
        metrics: 'Metrics',
        health: 'Health',
        logout: 'Log out'
      },
      login: {
        title: 'Welcome back',
        subtitle: 'Sign in to manage warehouse operations',
        email: 'Email',
        password: 'Password',
        submit: 'Sign in',
        loading: 'Signing in...'
      },
      dashboard: {
        kpis: 'Key Performance Indicators',
        liveFeed: 'Live Box Events',
        throughput: 'Throughput',
        occupancy: 'Occupancy',
        sla: 'SLA Compliance',
        chart: 'Operations Trend'
      },
      tables: {
        search: 'Search...',
        empty: 'No data available',
        export: 'Export CSV'
      },
      actions: {
        view: 'View details',
        confirm: 'Confirm',
        cancel: 'Cancel',
        delete: 'Delete',
        suspend: 'Suspend',
        resolve: 'Resolve'
      },
      confirmations: {
        title: 'Are you sure?',
        description: 'This action cannot be undone.'
      },
      timezone: {
        label: 'Timezone',
        kl: 'Asia/Kuala Lumpur',
        utc: 'UTC'
      },
      theme: {
        label: 'Theme',
        light: 'Light',
        dark: 'Dark',
        system: 'System'
      },
      language: {
        label: 'Language',
        en: 'English',
        zh: 'Chinese'
      },
      metrics: {
        title: 'Prometheus Metrics',
        description: 'Summaries from the /metrics endpoint.'
      },
      reports: {
        title: 'Reports',
        download: 'Download',
        description: 'Generate CSV and PDF exports on demand.'
      },
      health: {
        title: 'Health Overview',
        description: 'Monitor upstream services and background workers.'
      },
      errors: {
        boundaryTitle: 'Something went wrong',
        boundaryMessage: 'Please refresh the page or contact support if the problem persists.'
      }
    }
  },
  zh: {
    translation: {
      app: {
        title: '管理面板'
      },
      nav: {
        dashboard: '仪表板',
        boxes: '箱子',
        cases: '案件',
        items: '物品',
        users: '用户',
        audit: '审计日志',
        reports: '报告',
        metrics: '指标',
        health: '健康',
        logout: '退出登录'
      },
      login: {
        title: '欢迎回来',
        subtitle: '登录以管理仓库运营',
        email: '邮箱',
        password: '密码',
        submit: '登录',
        loading: '正在登录...'
      },
      dashboard: {
        kpis: '关键绩效指标',
        liveFeed: '实时箱子事件',
        throughput: '吞吐量',
        occupancy: '占用率',
        sla: 'SLA 合规',
        chart: '运营趋势'
      },
      tables: {
        search: '搜索...',
        empty: '没有数据',
        export: '导出 CSV'
      },
      actions: {
        view: '查看详情',
        confirm: '确认',
        cancel: '取消',
        delete: '删除',
        suspend: '暂停',
        resolve: '处理'
      },
      confirmations: {
        title: '确定执行操作吗？',
        description: '此操作无法撤销。'
      },
      timezone: {
        label: '时区',
        kl: '吉隆坡',
        utc: '世界标准时间'
      },
      theme: {
        label: '主题',
        light: '浅色',
        dark: '深色',
        system: '系统'
      },
      language: {
        label: '语言',
        en: '英文',
        zh: '中文'
      },
      metrics: {
        title: 'Prometheus 指标',
        description: '来自 /metrics 端点的摘要。'
      },
      reports: {
        title: '报告',
        download: '下载',
        description: '按需生成 CSV 和 PDF 导出。'
      },
      health: {
        title: '健康概览',
        description: '监控上游服务和后台任务。'
      },
      errors: {
        boundaryTitle: '发生错误',
        boundaryMessage: '请刷新页面或联系支持人员。'
      }
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
