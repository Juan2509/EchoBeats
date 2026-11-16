import {useEffect,useId,useRef} from 'react'
export function ConfirmDialog({message,answer}:{message:string;answer:(confirmed:boolean)=>void}){
  const ref=useRef<HTMLDialogElement>(null),id=useId()
  useEffect(()=>{ref.current?.showModal();return()=>ref.current?.close()},[])
  return <dialog ref={ref} className="album-dialog deletion-dialog" aria-labelledby={id} onCancel={event=>{event.preventDefault();answer(false)}}><h2 id={id}>Confirmar eliminación</h2><p>{message}</p><div className="editor-actions"><button type="button" className="secondary" autoFocus onClick={()=>answer(false)}>Cancelar</button><button type="button" className="danger-button" onClick={()=>answer(true)}>Eliminar</button></div></dialog>
}
