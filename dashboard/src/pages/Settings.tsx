import { useState } from 'react'
import { Save, Database, Shield } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({
    apiUrl: 'http://localhost:8000',
    enableReplay: true,
    enableAudit: true,
    policyMode: 'enforce',
  })

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="bg-white rounded-lg shadow divide-y">
        <div className="p-6">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Database className="h-5 w-5" />
            API Configuration
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API URL
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border rounded-lg"
                value={settings.apiUrl}
                onChange={(e) => setSettings({ ...settings, apiUrl: e.target.value })}
              />
            </div>
          </div>
        </div>

        <div className="p-6">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Shield className="h-5 w-5" />
            Security
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Policy Mode
              </label>
              <select
                className="w-full px-3 py-2 border rounded-lg"
                value={settings.policyMode}
                onChange={(e) => setSettings({ ...settings, policyMode: e.target.value })}
              >
                <option value="enforce">Enforce</option>
                <option value="warn">Warn Only</option>
                <option value="disabled">Disabled</option>
              </select>
            </div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.enableAudit}
                onChange={(e) => setSettings({ ...settings, enableAudit: e.target.checked })}
              />
              <span className="text-sm">Enable Audit Logging</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.enableReplay}
                onChange={(e) => setSettings({ ...settings, enableReplay: e.target.checked })}
              />
              <span className="text-sm">Enable Replay Recording</span>
            </label>
          </div>
        </div>

        <div className="p-6 bg-gray-50">
          <button className="flex items-center gap-2 px-4 py-2 bg-aegis-600 text-white rounded-lg hover:bg-aegis-700">
            <Save className="h-4 w-4" />
            Save Settings
          </button>
        </div>
      </div>
    </div>
  )
}
