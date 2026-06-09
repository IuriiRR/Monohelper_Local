import { useState } from 'react'
import { Alert, Card, Group, Loader, Select, Stack, Table, Text, Title } from '@mantine/core'
import { MonthPickerInput } from '@mantine/dates'
import { LineChart } from '@mantine/charts'
import { useMonthlyReport } from '../hooks/useMonthlyReport'
import { formatCurrency, formatDate } from '../lib/format'

export function Dashboard() {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7))
  const [jarId, setJarId] = useState<string | null>(null)
  const { data, isLoading, error } = useMonthlyReport(month)

  const jars = data?.jars ?? []
  const selected = jars.find((j) => j.id === jarId) ?? jars[0]
  const chartData = (selected?.transactions ?? []).map((t) => ({
    date: formatDate(t.time),
    balance: t.balance / 100,
  }))

  return (
    <Stack>
      <Group justify="space-between" align="flex-end">
        <Title order={2}>Monthly Report</Title>
        <MonthPickerInput
          label="Month"
          value={`${month}-01`}
          onChange={(v) => v && setMonth(v.slice(0, 7))}
          maw={200}
        />
      </Group>

      {isLoading && <Loader />}
      {error && <Alert color="red">{(error as Error).message}</Alert>}

      {!isLoading && !error && (
        <>
          <Table.ScrollContainer minWidth={700}>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Jar</Table.Th>
                  <Table.Th>Start</Table.Th>
                  <Table.Th>Current</Table.Th>
                  <Table.Th>Budget</Table.Th>
                  <Table.Th>Deposits</Table.Th>
                  <Table.Th>Spent</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {jars.map((j) => (
                  <Table.Tr key={j.id}>
                    <Table.Td>{j.title ?? j.id}</Table.Td>
                    <Table.Td>{formatCurrency(j.start_balance)}</Table.Td>
                    <Table.Td>{formatCurrency(j.current_balance)}</Table.Td>
                    <Table.Td>{formatCurrency(j.budget)}</Table.Td>
                    <Table.Td>{formatCurrency(j.total_deposits)}</Table.Td>
                    <Table.Td c={j.spent < 0 ? 'red' : undefined}>
                      {formatCurrency(j.spent)}
                    </Table.Td>
                  </Table.Tr>
                ))}
                {jars.length === 0 && (
                  <Table.Tr>
                    <Table.Td colSpan={6}>
                      <Text c="dimmed">No budget jars for this month.</Text>
                    </Table.Td>
                  </Table.Tr>
                )}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>

          {jars.length > 0 && (
            <Card withBorder>
              <Stack>
                <Group justify="space-between" align="flex-end">
                  <Title order={4}>Balance over time</Title>
                  <Select
                    data={jars.map((j) => ({ value: j.id, label: j.title ?? j.id }))}
                    value={selected?.id ?? null}
                    onChange={setJarId}
                    maw={240}
                  />
                </Group>
                {chartData.length > 0 ? (
                  <LineChart
                    h={300}
                    data={chartData}
                    dataKey="date"
                    series={[{ name: 'balance', label: 'Balance', color: 'blue.6' }]}
                    curveType="linear"
                    withDots={false}
                  />
                ) : (
                  <Text c="dimmed">No transactions for this jar in the selected month.</Text>
                )}
              </Stack>
            </Card>
          )}
        </>
      )}
    </Stack>
  )
}
