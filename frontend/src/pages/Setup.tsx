import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Button, Center, Group, Paper, Stack, Text, TextInput, Title } from '@mantine/core'
import { useApiKey } from '../hooks/useApiKey'

export function Setup() {
  const { key, setApiKey, clearApiKey } = useApiKey()
  const [input, setInput] = useState(key)
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  const hasLocalKey = Boolean(key)

  function handleSave() {
    setApiKey(input)
    navigate(from, { replace: true })
  }

  function handleClear() {
    clearApiKey()
    setInput('')
  }

  return (
    <Center h="100vh">
      <Paper shadow="md" p="xl" w={480}>
        <Stack gap="md">
          <Title order={3}>API Key Required</Title>
          <Text size="sm" c="dimmed">
            Enter your <code>INTERNAL_API_KEY</code> to access the app. The key is saved in your
            browser&apos;s local storage and sent as <code>X-API-Key</code> on every request.
          </Text>

          <TextInput
            label="API Key"
            placeholder="Paste your key here"
            value={input}
            onChange={(e) => setInput(e.currentTarget.value)}
            type="password"
          />

          <Group justify="space-between">
            <Button variant="subtle" color="red" onClick={handleClear} disabled={!hasLocalKey}>
              Clear saved key
            </Button>
            <Button onClick={handleSave} disabled={!input.trim()}>
              Save &amp; continue
            </Button>
          </Group>
        </Stack>
      </Paper>
    </Center>
  )
}
