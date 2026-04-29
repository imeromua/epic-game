export default function Spinner({ small = false }) {
  return <div className={small ? 'spinner spinner-sm' : 'spinner'} />
}
